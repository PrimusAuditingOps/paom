import base64
import io
from collections import defaultdict
from datetime import datetime
from odoo import models, api, fields, tools, _
from odoo.exceptions import UserError
from logging import getLogger

_logger = getLogger(__name__)

class PAOSalesBudget(models.Model):
    _name = "pao.sales.budget"
    _description = "PAO Annual Sales Budget"


    name = fields.Char(required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',copy=False, string='Currency', default=2, required=True)
    year = fields.Integer(string='Year', required=True, copy=False, default=lambda self: fields.Date.context_today(self).year)
    line_ids = fields.One2many('pao.sales.budget.line', 'budget_id', string='Lines', copy=False)

    crossovered_budget_ids = fields.Many2many(
        'crossovered.budget', string='Presupuestos de Egresos (Odoo)',
        help="Presupuestos nativos de egresos por cuenta analítica de esta misma "
             "temporada (uno por departamento, ej. IT, Finanzas), usados en conjunto "
             "para calcular el costo operativo presupuestado por servicio.")
    budgeted_exchange_rate = fields.Float(
        string='Tipo de Cambio Presupuestal (MXN por USD)', digits=(12, 4),
        help="Cuántos pesos equivalen a 1 dólar, para convertir los montos del "
             "presupuesto de egresos (en pesos) a dólares al calcular el costo "
             "operativo. Se captura una sola vez por temporada; no se actualiza "
             "solo con el tipo de cambio vigente de Odoo.")


    def action_view_actual_line(self):
        self.ensure_one()
        action = {
            'res_model': 'pao.sales.budget.actual.line',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,pivot',
            'name': _("Actual Lines"),
            'target': 'current',
            'context': {
                'search_default_group_by_region': 1,
                'search_default_group_by_customer_category': 1,
                'search_default_group_by_customer_name': 1,
            },
            'domain': [('budget_id', '=', self.id)],
        }
        return action

    def action_view_variance_report(self):
        self.ensure_one()
        action = {
            'res_model': 'pao.sales.budget.variance.report',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,pivot',
            'name': _("Presupuestado vs Real"),
            'target': 'current',
            'domain': [('budget_id', '=', self.id)],
        }
        return action

    def action_open_scheme_report_wizard(self):
        self.ensure_one()
        action = {
            'res_model': 'pao.sales.budget.scheme.report.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'name': _("Reporte por Esquema"),
            'target': 'new',
            'context': {'default_budget_id': self.id},
        }
        return action

    def action_view_budget_line(self):
        self.ensure_one()
        action = {
            'res_model': 'pao.sales.budget.line',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,pivot',
            'name': _("Budget Lines"),
            'target': 'current',  
            'context': {
                'search_default_group_by_region': 1,
                'search_default_group_by_customer_category': 1,
                'search_default_group_by_customer_name': 1,
                'default_budget_id': self.id,
            },
            'domain': [('budget_id', '=', self.id)],
        }
        return action

    def _populate_budget_lines(self, team, date_from, date_to, target_model='pao.sales.budget.line'):
        """Arma Clientes Clave / Promotor / Clientes Individuales para todas las
        regiones en `team`, en el rango date_from-date_to, escribiendo en
        target_model. La compartida por generate_budget_action (presupuesto,
        temporada anterior completa) y action_refresh_actual (lo real, temporada
        actual a la fecha) para no duplicar esta lógica en dos lugares.
        """
        customer_category = ["Clientes Clave", "Promotor", "Clientes Individuales"]
        for region in team:
            for customer_type in customer_category:
                if customer_type == "Clientes Clave":
                    groups = self.env["customergroups.group"].search([("pao_include_in_budget","=",True)])
                    for group in groups:
                        domain = [
                            ('invoice_date', '>=', date_from),
                            ('invoice_date', '<=', date_to),
                            ('product_tmpl_id.can_be_commissionable', '=', True),
                            ('group_id', '=', group.id),
                            ('partner_id.team_id', '=', region.id),
                        ]
                        self.create_budget_line_from_sales_invoicing_report(domain,region,customer_type,group.name,"simple",target_model=target_model)
                elif customer_type == "Promotor":
                    promotors = self.env["comisionpromotores.promotor"].search([("pao_include_in_budget","=",True)])
                    for promotor in promotors:
                        domain = [
                            ('invoice_date', '>=', date_from),
                            ('invoice_date', '<=', date_to),
                            ('product_tmpl_id.can_be_commissionable', '=', True),
                            ('promotor_id', '=', promotor.id),
                            ('partner_id.team_id', '=', region.id),
                        ]
                        self.create_budget_line_from_sales_invoicing_report(domain,region,customer_type,promotor.name,"simple",target_model=target_model)
                elif customer_type == "Clientes Individuales":
                    domain = [
                        ('invoice_date', '>=', date_from),
                        ('invoice_date', '<=', date_to),
                        ('product_tmpl_id.can_be_commissionable', '=', True),
                        ('partner_id.team_id', '=', region.id),
                        '|',
                            ('promotor_id', '=', False),
                            ('promotor_id.pao_include_in_budget', '=', False),
                        '|',
                            ('group_id', '=', False),
                            ('group_id.pao_include_in_budget', '=', False)
                    ]
                    self.create_budget_line_from_sales_invoicing_report(domain,region,customer_type,"Clientes Ind.","simple",target_model=target_model)

        # Rescata facturas de 'VENTA PUBLICO EN GENERAL' y las suma/crea dentro de
        # Clave/Promotor/Individuales según el cliente real de la cotización.
        self.create_budget_line_from_public_general(team, date_from=date_from, date_to=date_to, target_model=target_model)

    def generate_budget_action(self):
        self.ensure_one()
        team = self.env["crm.team"].search([("pao_include_in_budget","=",True)])
        date_from = '{0}-09-01'.format(self.year-1)
        date_to = '{0}-08-31'.format(self.year)

        self._populate_budget_lines(team, date_from, date_to, target_model='pao.sales.budget.line')

        # Clientes Nuevos: copia de Clientes Individuales (ya completo, incluyendo
        # lo rescatado de VENTA PUBLICO EN GENERAL) con las cantidades en 0, para
        # que el usuario defina a mano la meta de clientes nuevos a conseguir.
        # Corre después de _populate_budget_lines para que cualquier producto
        # nuevo agregado por el rescate de VENTA PUBLICO EN GENERAL también se copie.
        for region in team:
            budget_line = self.env['pao.sales.budget.line'].search([("region_id","=",region.id),("customer_category","=","Clientes Individuales")])
            to_create = []
            for line in budget_line:
                line_vals = {
                    'budget_id': self.id,
                    'region_id': line.region_id.id,
                    'customer_category': "Clientes Nuevos",
                    'customer_name': "Clientes Nuevos",
                    'product_id': line.product_id.id,
                    'price_unit': line.price_unit,
                    'm01': 0,
                    'm02': 0,
                    'm03': 0,
                    'm04': 0,
                    'm05': 0,
                    'm06': 0,
                    'm07': 0,
                    'm08': 0,
                    'm09': 0,
                    'm10': 0,
                    'm11': 0,
                    'm12': 0,
                }
                to_create.append(line_vals)

            # Crear en batches
            created = []
            BATCH = 200
            for i in range(0, len(to_create), BATCH):
                chunk = to_create[i:i+BATCH]
                created_chunk = budget_line.sudo().create(chunk)
                created += created_chunk

        # Se recalcula al final, sobre todas las líneas del presupuesto, para
        # cubrir de un solo golpe tanto lo creado por _populate_budget_lines
        # como las líneas de "Clientes Nuevos" generadas arriba.
        self.line_ids._compute_and_set_provider_cost_rate()
        self.line_ids._compute_and_set_operational_cost_rate()

        return {'message': _('Se han creado las líneas de presupuesto')}

    def _get_operational_cost_rates(self):
        """Devuelve (rate_staff, {scheme_id: rate_esquema}) para este
        presupuesto, cruzando los presupuestos nativos de egresos
        (crossovered_budget_ids - uno por departamento) contra el presupuesto
        de ingresos (line_ids) de esta misma temporada.

        rate_staff: tasa única, aplica a cualquier línea sin importar esquema
        (cuentas analíticas sin pao_sales_budget_scheme_ids = staff/overhead).

        rate_esquema: una tasa por esquema, solo aplica a líneas de ese
        esquema (cuentas analíticas cuyo pao_sales_budget_scheme_ids incluya
        ese esquema). Si un esquema no tiene ninguna cuenta analítica
        asignada, no aparece en el diccionario (equivale a tasa 0 - ese
        servicio no necesita área especializada, solo le pega staff).

        Los montos de crossovered.budget.lines están en la moneda de la
        compañía (pesos); se convierten a dólares con budgeted_exchange_rate
        (pesos por dólar) antes de cruzarlos contra total_amount (ya en
        dólares) - no se usa el tipo de cambio vigente de Odoo porque un
        presupuesto no debe moverse solo porque cambió el spot del día.
        """
        self.ensure_one()
        if not self.crossovered_budget_ids or not self.budgeted_exchange_rate:
            return 0.0, {}

        staff_expense = 0.0
        scheme_expense = defaultdict(float)
        for bline in self.crossovered_budget_ids.crossovered_budget_line:
            if not bline.analytic_account_id:
                continue
            amount_usd = abs(bline.planned_amount) / self.budgeted_exchange_rate
            schemes = bline.analytic_account_id.pao_sales_budget_scheme_ids
            if not schemes:
                staff_expense += amount_usd
            else:
                for scheme in schemes:
                    scheme_expense[scheme.id] += amount_usd

        total_revenue = sum(self.line_ids.mapped('total_amount'))
        rate_staff = (staff_expense / total_revenue) if total_revenue else 0.0

        scheme_revenue = defaultdict(float)
        for line in self.line_ids:
            if line.pao_sales_budget_scheme_id:
                scheme_revenue[line.pao_sales_budget_scheme_id.id] += line.total_amount

        rate_scheme = {
            scheme_id: expense / scheme_revenue[scheme_id]
            for scheme_id, expense in scheme_expense.items()
            if scheme_revenue.get(scheme_id)
        }
        return rate_staff, rate_scheme

    def action_calculate_provider_cost_rate(self):
        """Recalcula provider_cost_rate y operational_cost_rate (y con ellas
        provider_cost_amount / operational_cost_amount / net_profit_amount /
        net_profit_pct) sobre las líneas ya existentes de este presupuesto.
        Necesario para presupuestos generados antes de que existiera este
        cálculo, o si se quiere refrescar contra compras/presupuesto de
        egresos más recientes sin regenerar el presupuesto completo (lo cual
        ni siquiera es posible desde la UI una vez que ya tiene líneas, porque
        el botón "Generate Budget" se oculta en ese caso).
        """
        self.ensure_one()
        self.line_ids._compute_and_set_provider_cost_rate()
        self.line_ids._compute_and_set_operational_cost_rate()
        return {'message': _('Se recalculó la rentabilidad presupuestada')}

    def action_refresh_actual(self):
        """Recalcula lo realmente facturado (pao.sales.budget.actual.line) de la
        temporada que este presupuesto está proyectando, a la fecha. Borra y
        vuelve a generar desde cero (no incremental) para que siempre refleje el
        estado real de facturación al momento de darle clic.

        OJO con las fechas: self.year es el año en que CIERRA la temporada BASE
        (ej. year=2025 -> base Sep-2024 a Ago-2025, que es lo que usa
        generate_budget_action). La temporada que este presupuesto proyecta -y
        contra la que se compara lo real- es la siguiente: Sep-2025 a Ago-2026.
        """
        self.ensure_one()
        ActualLine = self.env['pao.sales.budget.actual.line'].sudo()
        ActualLine.search([('budget_id', '=', self.id)]).unlink()

        team = self.env["crm.team"].search([("pao_include_in_budget","=",True)])
        date_from = '{0}-09-01'.format(self.year)
        season_end = '{0}-08-31'.format(self.year + 1)
        today_str = fields.Date.context_today(self).strftime('%Y-%m-%d')
        date_to = min(today_str, season_end)

        self._populate_budget_lines(team, date_from, date_to, target_model='pao.sales.budget.actual.line')

        return {'message': _('Se actualizó lo facturado real')}

    def action_export_variance_excel(self):
        """Genera y descarga el Excel de Presupuestado vs Real de este presupuesto,
        una fila por región+categoría+cliente+producto, con columnas por mes
        (Presupuestado / Real / Variación %) más una columna de total de temporada,
        coloreadas igual que la vista en Odoo (rojo = debajo del presupuesto,
        verde = en el presupuesto, amarillo = arriba del presupuesto, azul = venta
        sin presupuesto).
        """
        self.ensure_one()
        from odoo.tools.misc import xlsxwriter

        VR = self.env['pao.sales.budget.variance.report'].sudo()
        rows = VR.search([('budget_id', '=', self.id)])

        months_order = ['09', '10', '11', '12', '01', '02', '03', '04', '05', '06', '07', '08']
        month_labels = {'01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun',
                         '07': 'Jul', '08': 'Ago', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic'}

        grouped = defaultdict(lambda: {m: {'budgeted': 0.0, 'actual': 0.0} for m in months_order})
        meta = {}
        for r in rows:
            key = (r.region_id.id, r.customer_category, r.customer_name, r.product_id.id)
            grouped[key][r.month]['budgeted'] += r.budgeted_qty
            grouped[key][r.month]['actual'] += r.actual_qty
            meta[key] = (r.region_id.name or '', r.customer_category or '', r.customer_name or '', r.product_id.display_name or '')

        def variance(budgeted, actual):
            """Regresa (fracción de variación, sin_presupuesto). Cuando no hay
            presupuesto pero sí venta, se usa un sentinel alto (999.9%) para que
            resalte, en vez de dividir entre cero."""
            if budgeted == 0:
                return (9.999, True) if actual > 0 else (0.0, False)
            return ((actual - budgeted) / budgeted, False)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Presupuesto vs Real')

        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center'})
        label_fmt = workbook.add_format({'border': 1})
        qty_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        pct_fmts = {
            'danger': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#FFC7CE', 'font_color': '#9C0006'}),
            'success': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#C6EFCE', 'font_color': '#006100'}),
            'warning': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#FFEB9C', 'font_color': '#9C6500'}),
            'unbudgeted': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#BDD7EE', 'font_color': '#1F4E78'}),
        }

        def pick_style(pct, unbudgeted):
            if unbudgeted:
                return pct_fmts['unbudgeted']
            if pct < -0.0001:
                return pct_fmts['danger']
            elif pct > 0.0001:
                return pct_fmts['warning']
            return pct_fmts['success']

        # Encabezados (2 filas: mes y sub-columna)
        worksheet.merge_range(0, 0, 1, 0, 'Región', header_fmt)
        worksheet.merge_range(0, 1, 1, 1, 'Categoría', header_fmt)
        worksheet.merge_range(0, 2, 1, 2, 'Cliente', header_fmt)
        worksheet.merge_range(0, 3, 1, 3, 'Producto', header_fmt)
        col = 4
        for m in months_order:
            worksheet.merge_range(0, col, 0, col + 2, month_labels[m], header_fmt)
            worksheet.write(1, col, 'Presup.', header_fmt)
            worksheet.write(1, col + 1, 'Real', header_fmt)
            worksheet.write(1, col + 2, 'Var %', header_fmt)
            col += 3
        worksheet.merge_range(0, col, 0, col + 2, 'Total Temporada', header_fmt)
        worksheet.write(1, col, 'Presup.', header_fmt)
        worksheet.write(1, col + 1, 'Real', header_fmt)
        worksheet.write(1, col + 2, 'Var %', header_fmt)
        total_col = col

        worksheet.set_column(0, 3, 22)
        worksheet.set_column(4, total_col + 2, 10)
        worksheet.freeze_panes(2, 4)

        row = 2
        for key, months in grouped.items():
            region_name, category, name, product_name = meta[key]
            worksheet.write(row, 0, region_name, label_fmt)
            worksheet.write(row, 1, category, label_fmt)
            worksheet.write(row, 2, name, label_fmt)
            worksheet.write(row, 3, product_name, label_fmt)

            col = 4
            total_b = total_a = 0.0
            for m in months_order:
                b = months[m]['budgeted']
                a = months[m]['actual']
                total_b += b
                total_a += a
                pct, unbudgeted = variance(b, a)
                worksheet.write(row, col, b, qty_fmt)
                worksheet.write(row, col + 1, a, qty_fmt)
                worksheet.write(row, col + 2, pct, pick_style(pct, unbudgeted))
                col += 3

            pct_total, unbudgeted_total = variance(total_b, total_a)
            worksheet.write(row, total_col, total_b, qty_fmt)
            worksheet.write(row, total_col + 1, total_a, qty_fmt)
            worksheet.write(row, total_col + 2, pct_total, pick_style(pct_total, unbudgeted_total))
            row += 1

        workbook.close()
        xlsx_data = output.getvalue()

        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Presupuesto_vs_Real_%s.xlsx' % (self.name or self.id),
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def create_budget_line(self,domain,region,customer_type,customer_name,avg_type):
        
        budget_line = self.env['pao.sales.budget.line']
        AML = self.env['account.move.line']
        target_currency = self.currency_id
        

        lines = AML.search(domain)
        lines = lines.sorted(key=lambda l: l.move_id.invoice_date or date.min)
        #if not lines:
        #    _logger.info("No se encontraron facturas en el rango %s - %s", date_from, date_to)
        #    return {'message': 'No se encontraron líneas de factura en el rango especificado.', 'created': 0}

        # Estructura de agregación por (product_id, partner_id)
        # para cada mes 1..12 almacenamos:
        # - qty_by_month[m] => sum qty
        # - price_list[m] => lista de unit_converted (para promedio simple)
        data = defaultdict(lambda: {
            'qty_by_month': defaultdict(float),
            'price_list_by_month': defaultdict(list),
        })

        def month_index(date_val):
            # date_val puede ser date/datetime/str
            if isinstance(date_val, str):
                try:
                    dt = fields.Date.from_string(date_val)
                except Exception:
                    dt = fields.Date.context_today(self)
            elif isinstance(date_val, (datetime,)):
                dt = date_val.date()
            else:
                dt = date_val
            return dt.month

        # Procesar cada línea
        for ln in lines:
            inv = ln.move_id
            inv_date = inv.invoice_date or inv.invoice_date or fields.Date.context_today(self)
            m = month_index(inv_date)
            product = ln.product_id.product_tmpl_id

            unit = float(ln.price_unit or 0.0)
            qty = float(getattr(ln, 'quantity', 0.00) or 0.0)

            
            src_currency = inv.currency_id or inv.company_id.currency_id or self.env.company.currency_id
            
            try:
                unit_conv = src_currency._convert(unit, target_currency, inv.company_id, inv_date)
            except Exception as e:
                _logger.exception("Fallo convert currency for line %s: %s", ln.id, e)
                unit_conv = unit

            key = (product.id)
            data[key]['qty_by_month'][m] += qty
            if avg_type == 'simple':
                # para promedio simple guardamos la medida convertida en la lista (por mes)
                data[key]['price_list_by_month'][m].append(unit_conv)
            else:
                # para ponderado guardamos unit_conv * qty y sumaremos luego
                data[key].setdefault('priceqty_by_month', defaultdict(float))
                data[key]['priceqty_by_month'][m] += unit_conv * qty
                # keep qty_by_month for denominator

        

        to_create = []
        for (prod_id), vals in data.items():
            # calcular promedio por todo el periodo (simple) o por mes según quieras:
            # El requerimiento: "promedio simple en base al rango de la fecha" -> calculamos promedio simple sobre todas las líneas del año
            all_prices = []
            for m in range(1, 13):
                all_prices.extend(vals['price_list_by_month'].get(m, []))
            avg_price = float(sum(all_prices) / len(all_prices)) if all_prices else 0.0

            # llenar meses m01..m12 con la suma de qty por mes
            months = {}
            for m in range(1, 13):
                field_name = f"m{m:02d}"
                months[field_name] = float(vals['qty_by_month'].get(m, 0.0))

            line_vals = {
                'budget_id': self.id,
                'region_id': region.id,
                'customer_category': customer_type,
                'customer_name': customer_name,
                'product_id': prod_id,
                'price_unit': avg_price,
                **months,
            }
            to_create.append(line_vals)

        # Crear en batches
        created = []
        BATCH = 200
        for i in range(0, len(to_create), BATCH):
            chunk = to_create[i:i+BATCH]
            created_chunk = budget_line.sudo().create(chunk)
            created += created_chunk

    def create_budget_line_from_sales_invoicing_report(self,domain,region,customer_type,customer_name,avg_type,target_model='pao.sales.budget.line'):
        """Igual que create_budget_line pero lee de sales.invoicing.report en vez de
        account.move.line directamente. Esa vista ya incluye las notas de credito/DV
        (out_refund) y resuelve, por linea, el producto original (aunque la DV se
        facture con un producto de devoluciones distinto ante el SAT) y si la
        devolucion fue total (resta la cantidad completa) o solo monetaria/parcial
        (cantidad en 0, no se descuenta producto). Ver pao_sales_invoicing_report
        para el detalle de esa logica.

        target_model permite reusar exactamente esta misma lógica para llenar
        tanto pao.sales.budget.line (el presupuesto) como pao.sales.budget.actual.line
        (lo realmente facturado), ambos con la misma forma de campos.

        Solo cuando target_model es pao.sales.budget.actual.line: si el cliente
        de la factura (res.partner.sales_customer_type, de pao_customer_segmentation)
        es 'new', 'recovered' o 'lost' -es decir, no facturó en la temporada
        anterior a la actual-, esa línea se manda a "Clientes Nuevos" en vez de a
        customer_type/customer_name, porque no tiene una base de comparación en
        su categoría normal.
        """
        budget_line = self.env[target_model]
        SIR = self.env['sales.invoicing.report'].sudo()
        AML = self.env['account.move.line'].sudo()
        target_currency = self.currency_id
        is_actual = target_model == 'pao.sales.budget.actual.line'
        NEW_CUSTOMER_TYPES = ('new', 'recovered', 'lost')

        lines = SIR.search(domain)

        # Estructura de agregación por product_id, igual que create_budget_line
        data = defaultdict(lambda: {
            'qty_by_month': defaultdict(float),
            'price_list_by_month': defaultdict(list),
        })

        def month_index(date_val):
            if isinstance(date_val, str):
                try:
                    dt = fields.Date.from_string(date_val)
                except Exception:
                    dt = fields.Date.context_today(self)
            elif isinstance(date_val, datetime):
                dt = date_val.date()
            else:
                dt = date_val
            return dt.month

        for ln in lines:
            m = month_index(ln.invoice_date)
            product = ln.product_tmpl_id
            qty = float(ln.quantity or 0.0)

            if is_actual and ln.partner_id.sales_customer_type in NEW_CUSTOMER_TYPES:
                row_type, row_name = "Clientes Nuevos", "Clientes Nuevos"
            else:
                row_type, row_name = customer_type, customer_name

            key = (row_type, row_name, product.id)
            data[key]['qty_by_month'][m] += qty

            # Una devolución (qty <= 0) no es un dato de precio de venta, solo
            # debe afectar la cantidad. El promedio de precio se calcula únicamente
            # con líneas de venta reales.
            if qty > 0:
                aml = AML.browse(ln.id)
                inv = aml.move_id
                unit = float(aml.price_unit or 0.0)
                src_currency = inv.currency_id or inv.company_id.currency_id or self.env.company.currency_id

                try:
                    unit_conv = src_currency._convert(unit, target_currency, inv.company_id, ln.invoice_date)
                except Exception as e:
                    _logger.exception("Fallo convert currency for line %s: %s", ln.id, e)
                    unit_conv = unit

                if avg_type == 'simple':
                    data[key]['price_list_by_month'][m].append(unit_conv)
                else:
                    data[key].setdefault('priceqty_by_month', defaultdict(float))
                    data[key]['priceqty_by_month'][m] += unit_conv * qty

        to_create = []
        for (row_type, row_name, prod_id), vals in data.items():
            all_prices = []
            for m in range(1, 13):
                all_prices.extend(vals['price_list_by_month'].get(m, []))
            avg_price = float(sum(all_prices) / len(all_prices)) if all_prices else 0.0

            months = {}
            for m in range(1, 13):
                field_name = f"m{m:02d}"
                months[field_name] = float(vals['qty_by_month'].get(m, 0.0))

            # "Clientes Nuevos" puede recibir aportes de varias llamadas distintas
            # (una llamada por grupo/promotor/individuales) para el mismo producto,
            # así que aquí sí hay que sumar a una línea existente en vez de asumir
            # que la clave es única por llamada, como sí lo era antes de este redirect.
            existing = budget_line.sudo().search([
                ('budget_id', '=', self.id),
                ('region_id', '=', region.id),
                ('customer_category', '=', row_type),
                ('customer_name', '=', row_name),
                ('product_id', '=', prod_id),
            ], limit=1)

            if existing:
                existing.sudo().write({field: existing[field] + months[field] for field in months})
            else:
                to_create.append({
                    'budget_id': self.id,
                    'region_id': region.id,
                    'customer_category': row_type,
                    'customer_name': row_name,
                    'product_id': prod_id,
                    'price_unit': avg_price,
                    **months,
                })

        # Crear en batches
        created = []
        BATCH = 200
        for i in range(0, len(to_create), BATCH):
            chunk = to_create[i:i+BATCH]
            created_chunk = budget_line.sudo().create(chunk)
            created += created_chunk

    def create_budget_line_from_public_general(self, team, date_from=None, date_to=None, target_model='pao.sales.budget.line'):
        """Rescata facturas emitidas al contacto 'VENTA PUBLICO EN GENERAL'.

        Facturación usa ese contacto genérico (sin equipo/grupo/promotor) cuando
        el cliente real no pide factura a su nombre, pero la cotización que dio
        origen a esa factura sí queda ligada al cliente real. Se usa esa
        cotización (account.move.line.sale_line_ids.order_id) para resolver a
        qué equipo/grupo/promotor pertenece la venta, y las cantidades se suman
        a la línea existente en target_model para ese cliente si ya existe
        (creada por las ramas normales de _populate_budget_lines), o se crea una
        nueva si no. Si la línea de factura no tiene cotización ligada, se omite:
        no hay forma de saber a quién pertenece esa venta.

        Igual que en create_budget_line_from_sales_invoicing_report: solo cuando
        target_model es pao.sales.budget.actual.line, si el cliente real de la
        cotización es 'new', 'recovered' o 'lost' se manda a "Clientes Nuevos"
        con prioridad sobre Clave/Promotor/Individuales.
        """
        budget_line = self.env[target_model].sudo()
        SIR = self.env['sales.invoicing.report'].sudo()
        AML = self.env['account.move.line'].sudo()
        target_currency = self.currency_id
        team_ids = set(team.ids)
        is_actual = target_model == 'pao.sales.budget.actual.line'
        NEW_CUSTOMER_TYPES = ('new', 'recovered', 'lost')

        public_partner = self.env['res.partner'].sudo().search(
            [('name', '=', 'VENTA PUBLICO EN GENERAL')], limit=1)
        if not public_partner:
            _logger.warning(
                "No se encontró el contacto 'VENTA PUBLICO EN GENERAL', se omite el rescate de facturas.")
            return

        date_from = date_from or '{0}-09-01'.format(self.year - 1)
        date_to = date_to or '{0}-08-31'.format(self.year)
        domain = [
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('product_tmpl_id.can_be_commissionable', '=', True),
            ('partner_id', '=', public_partner.id),
        ]
        lines = SIR.search(domain)

        def month_index(date_val):
            if isinstance(date_val, str):
                try:
                    dt = fields.Date.from_string(date_val)
                except Exception:
                    dt = fields.Date.context_today(self)
            elif isinstance(date_val, datetime):
                dt = date_val.date()
            else:
                dt = date_val
            return dt.month

        # Agrupación por (region, categoría, nombre, producto) resueltos desde la cotización
        data = defaultdict(lambda: {
            'qty_by_month': defaultdict(float),
            'price_list_by_month': defaultdict(list),
        })

        for ln in lines:
            aml = AML.browse(ln.id)
            orders = aml.sale_line_ids.order_id
            if not orders:
                _logger.warning(
                    "Línea de factura %s de 'VENTA PUBLICO EN GENERAL' sin cotización ligada, se omite.",
                    aml.id)
                continue
            if len(orders) > 1:
                _logger.warning(
                    "Línea de factura %s de 'VENTA PUBLICO EN GENERAL' ligada a varias cotizaciones %s, se usa la primera.",
                    aml.id, orders.ids)
            real_partner = orders[0].partner_id
            region = real_partner.team_id
            if not region or region.id not in team_ids:
                continue

            if is_actual and real_partner.sales_customer_type in NEW_CUSTOMER_TYPES:
                customer_type = "Clientes Nuevos"
                customer_name = "Clientes Nuevos"
            elif real_partner.cgg_group_id and real_partner.cgg_group_id.pao_include_in_budget:
                customer_type = "Clientes Clave"
                customer_name = real_partner.cgg_group_id.name
            elif real_partner.promotor_id and real_partner.promotor_id.pao_include_in_budget:
                customer_type = "Promotor"
                customer_name = real_partner.promotor_id.name
            else:
                customer_type = "Clientes Individuales"
                customer_name = "Clientes Ind."

            m = month_index(ln.invoice_date)
            product = ln.product_tmpl_id
            qty = float(ln.quantity or 0.0)

            key = (region.id, customer_type, customer_name, product.id)
            data[key]['qty_by_month'][m] += qty

            # Igual que en create_budget_line_from_sales_invoicing_report: las
            # devoluciones no son un dato de precio de venta, solo afectan cantidad.
            if qty > 0:
                inv = aml.move_id
                unit = float(aml.price_unit or 0.0)
                src_currency = inv.currency_id or inv.company_id.currency_id or self.env.company.currency_id
                try:
                    unit_conv = src_currency._convert(unit, target_currency, inv.company_id, ln.invoice_date)
                except Exception as e:
                    _logger.exception("Fallo convert currency for line %s: %s", ln.id, e)
                    unit_conv = unit
                data[key]['price_list_by_month'][m].append(unit_conv)

        to_create = []
        for (region_id, customer_type, customer_name, prod_id), vals in data.items():
            all_prices = []
            for m in range(1, 13):
                all_prices.extend(vals['price_list_by_month'].get(m, []))
            avg_price = float(sum(all_prices) / len(all_prices)) if all_prices else 0.0

            months = {}
            for m in range(1, 13):
                field_name = f"m{m:02d}"
                months[field_name] = float(vals['qty_by_month'].get(m, 0.0))

            existing = budget_line.search([
                ('budget_id', '=', self.id),
                ('region_id', '=', region_id),
                ('customer_category', '=', customer_type),
                ('customer_name', '=', customer_name),
                ('product_id', '=', prod_id),
            ], limit=1)

            if existing:
                # Solo se suman las cantidades a la línea existente; el precio
                # promedio ya guardado no se recalcula (no hay forma de saber
                # cuántas líneas originales lo componen para ponderar bien).
                existing.write({field: existing[field] + months[field] for field in months})
            else:
                to_create.append({
                    'budget_id': self.id,
                    'region_id': region_id,
                    'customer_category': customer_type,
                    'customer_name': customer_name,
                    'product_id': prod_id,
                    'price_unit': avg_price,
                    **months,
                })

        BATCH = 200
        for i in range(0, len(to_create), BATCH):
            chunk = to_create[i:i+BATCH]
            budget_line.create(chunk)


class PAOSalesBudgetLine(models.Model):
    _name = "pao.sales.budget.line"
    _description = "PAO Annual Sales Budget Lines"
    _order = "region_id, customer_category, customer_name, product_id_reference ASC"

    budget_id = fields.Many2one('pao.sales.budget', string='Budget', required=True, ondelete='cascade')
    region_id = fields.Many2one('crm.team', string='Region',ondelete='restrict',)
    customer_category = fields.Selection([
        ('Clientes Clave', 'Clientes Clave'),
        ('Promotor', 'Promotor'),
        ('Clientes Individuales', 'Clientes Individuales'),
        ('Clientes Nuevos', 'Clientes Nuevos'),
    ], string='Customer Category')
    customer_name = fields.Char(string='Customer Name')
    product_id = fields.Many2one('product.template', string='Producto')
    currency_id = fields.Many2one(related='budget_id.currency_id')
    product_id_reference = fields.Char(related='product_id.default_code', store=True)
    pao_sales_budget_scheme_id = fields.Many2one(related='product_id.pao_sales_budget_scheme_id',store=True)
    price_unit = fields.Monetary(string='Average Price', currency_field='currency_id')
    # Quantity Month
    m01 = fields.Float("Jan", default=0.0)
    m02 = fields.Float("Feb", default=0.0)
    m03 = fields.Float("Mar", default=0.0)
    m04 = fields.Float("Apr", default=0.0)
    m05 = fields.Float("May", default=0.0)
    m06 = fields.Float("Jun", default=0.0)
    m07 = fields.Float("Jul", default=0.0)
    m08 = fields.Float("Aug", default=0.0)
    m09 = fields.Float("Sep", default=0.0)
    m10 = fields.Float("Oct", default=0.0)
    m11 = fields.Float("Nov", default=0.0)
    m12 = fields.Float("Dec", default=0.0)
    # Amount Month
    m01_amount = fields.Float("Total Amount Jan", compute='_compute_total_jan', store=True)
    m02_amount = fields.Float("Total Amount Feb", compute='_compute_total_feb', store=True)
    m03_amount = fields.Float("Total Amount Mar", compute='_compute_total_mar', store=True)
    m04_amount = fields.Float("Total Amount Apr", compute='_compute_total_apr', store=True)
    m05_amount = fields.Float("Total Amount May", compute='_compute_total_may', store=True)
    m06_amount = fields.Float("Total Amount Jun", compute='_compute_total_jun', store=True)
    m07_amount = fields.Float("Total Amount Jul", compute='_compute_total_jul', store=True)
    m08_amount = fields.Float("Total Amount Aug", compute='_compute_total_aug', store=True)
    m09_amount = fields.Float("Total Amount Sep", compute='_compute_total_sep', store=True)
    m10_amount = fields.Float("Total Amount Oct", compute='_compute_total_oct', store=True)
    m11_amount = fields.Float("Total Amount Nov", compute='_compute_total_nov', store=True)
    m12_amount = fields.Float("Total Amount Dec", compute='_compute_total_dec', store=True)


    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total', currency_field='currency_id', store=True)
    total_quantity = fields.Float(string='Total Quantity', compute='_compute_total', store=True)

    # Rentabilidad presupuestada (solo costo de proveedor, sin costo operativo)
    # provider_cost_rate y net_profit_pct son porcentajes: sumarlos entre
    # varias líneas agrupadas no tiene sentido (a diferencia de los montos en
    # dólares, que sí son aditivos), así que se desactiva la agregación por
    # defecto de Odoo (group_operator='sum') para que una fila agrupada los
    # muestre en blanco en vez de una suma sin sentido.
    provider_cost_rate = fields.Float(
        string='Provider Cost Rate', copy=False, default=0.0, group_operator=None,
        help="Tasa ponderada de costo de proveedor para este servicio, calculada de las "
             "compras de la temporada base (service_start_date) ligadas a una venta. Se "
             "recalcula al generar el presupuesto o al cambiar el producto de la línea.")
    provider_cost_amount = fields.Monetary(
        string='Provider Cost Amount', compute='_compute_net_profit',
        currency_field='currency_id', store=True)
    operational_cost_rate = fields.Float(
        string='Operational Cost Rate', copy=False, default=0.0, group_operator=None,
        help="Tasa de costo operativo presupuestado (staff + área especializada del "
             "esquema de este servicio), calculada del presupuesto de egresos nativo "
             "de Odoo ligado al presupuesto. Se recalcula al generar el presupuesto, "
             "al cambiar el producto de la línea, o con el botón Calcular Rentabilidad.")
    operational_cost_amount = fields.Monetary(
        string='Operational Cost Amount', compute='_compute_net_profit',
        currency_field='currency_id', store=True)
    net_profit_amount = fields.Monetary(
        string='Net Profit Amount', compute='_compute_net_profit',
        currency_field='currency_id', store=True)
    net_profit_pct = fields.Float(
        string='Net Profit %', compute='_compute_net_profit', store=True, group_operator=None)

    # ------------------------------------------------------------------
    # Notificaciones en vivo (bus) para que otros usuarios con la lista
    # abierta vean los cambios de sus compañeros sin tener que refrescar.
    # Escucha el JS registrado como js_class="pao_sales_budget_line_list"
    # en pao_sales_budget_line_view_tree.
    # ------------------------------------------------------------------
    _PAO_BUS_CHANNEL = 'pao_sales_budget_line'

    def _pao_bus_notify(self, notif_type):
        budget_ids = set(self.mapped('budget_id').ids)
        for budget_id in budget_ids:
            self.env['bus.bus']._sendone(
                self._PAO_BUS_CHANNEL,
                'pao_sales_budget_line/changed',
                {
                    'type': notif_type,
                    'budget_id': budget_id,
                    'ids': self.filtered(lambda l: l.budget_id.id == budget_id).ids,
                },
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._pao_bus_notify('create')
        return records

    def write(self, vals):
        res = super().write(vals)
        self._pao_bus_notify('update')
        return res

    def unlink(self):
        budget_ids = self.mapped('budget_id').ids
        ids = self.ids
        res = super().unlink()
        for budget_id in budget_ids:
            self.env['bus.bus']._sendone(
                self._PAO_BUS_CHANNEL,
                'pao_sales_budget_line/changed',
                {'type': 'unlink', 'budget_id': budget_id, 'ids': ids},
            )
        return res

    @api.depends('m01','price_unit')
    def _compute_total_jan(self):
        for rec in self:
            rec.m01_amount = rec.m01 * (rec.price_unit or 0.0)
    
    @api.depends('m02','price_unit')
    def _compute_total_feb(self):
        for rec in self:
            rec.m02_amount = rec.m02 * (rec.price_unit or 0.0)    
    @api.depends('m03','price_unit')
    def _compute_total_mar(self):
        for rec in self:
            rec.m03_amount = rec.m03 * (rec.price_unit or 0.0)  
    @api.depends('m04','price_unit')
    def _compute_total_apr(self):
        for rec in self:
            rec.m04_amount = rec.m04 * (rec.price_unit or 0.0)  
    @api.depends('m05','price_unit')
    def _compute_total_may(self):
        for rec in self:
            rec.m05_amount = rec.m05 * (rec.price_unit or 0.0)  
    @api.depends('m06','price_unit')
    def _compute_total_jun(self):
        for rec in self:
            rec.m06_amount = rec.m06 * (rec.price_unit or 0.0)  
    @api.depends('m07','price_unit')
    def _compute_total_jul(self):
        for rec in self:
            rec.m07_amount = rec.m07 * (rec.price_unit or 0.0)  
    @api.depends('m08','price_unit')
    def _compute_total_aug(self):
        for rec in self:
            rec.m08_amount = rec.m08 * (rec.price_unit or 0.0)  
    @api.depends('m09','price_unit')
    def _compute_total_sep(self):
        for rec in self:
            rec.m09_amount = rec.m09 * (rec.price_unit or 0.0)  
    @api.depends('m10','price_unit')
    def _compute_total_oct(self):
        for rec in self:
            rec.m10_amount = rec.m10 * (rec.price_unit or 0.0)  
    @api.depends('m11','price_unit')
    def _compute_total_nov(self):
        for rec in self:
            rec.m11_amount = rec.m11 * (rec.price_unit or 0.0)  
    @api.depends('m12','price_unit')
    def _compute_total_dec(self):
        for rec in self:
            rec.m12_amount = rec.m12 * (rec.price_unit or 0.0)  
   

    @api.depends('m01','m02','m03','m04','m05','m06','m07','m08','m09','m10','m11','m12','price_unit')
    def _compute_total(self):
        for rec in self:
            qty_sum = sum((rec.m01,rec.m02,rec.m03,rec.m04,rec.m05,rec.m06,rec.m07,rec.m08,rec.m09,rec.m10,rec.m11,rec.m12))
            rec.total_amount = qty_sum * (rec.price_unit or 0.0)
            rec.total_quantity = qty_sum

    @api.depends('total_amount', 'provider_cost_rate', 'operational_cost_rate')
    def _compute_net_profit(self):
        for rec in self:
            rec.provider_cost_amount = rec.total_amount * rec.provider_cost_rate
            rec.operational_cost_amount = rec.total_amount * rec.operational_cost_rate
            rec.net_profit_amount = rec.total_amount - rec.provider_cost_amount - rec.operational_cost_amount
            rec.net_profit_pct = (rec.net_profit_amount / rec.total_amount) if rec.total_amount else 0.0

    @api.model
    def _get_provider_cost_rates(self, template_ids, date_from, date_to):
        """Tasa ponderada de costo de proveedor por producto (product.template),
        para el rango de fechas dado.

        Ponderación por volumen: se toman todas las líneas de compra confirmadas
        (state distinto de cancel) de ese producto, con service_start_date dentro
        del rango, cuya orden tenga audit_fee_id (tipo de honorario de auditoría)
        asignado. Cada línea pesa según su product_qty, así un proveedor con más
        volumen histórico pesa más en la tasa resultante que uno con pocos
        servicios, sin necesidad de agrupar por proveedor explícitamente.

        Se usa service_start_date (no la fecha de la orden ni la de factura de
        venta) porque el servicio casi nunca se presta en el mismo mes en que se
        factura al cliente.

        El % pagado se lee directamente de
        partner_id.audit_fee_percentages_ids (filtrado por el audit_fee_id de
        la orden), NO se deduce de price_unit/sra_sale_line_price_unit. Esto es
        deliberado: la compra puede estar en una moneda distinta a la venta
        (MXN vs USD), y el tipo de cambio con el que se convirtió price_unit en
        su momento no queda historizado en ningún lado (solo existe un valor
        vigente por moneda en servicereferralagreement.auditorexchangerate, sin
        fecha) - reconstruir el % desde esos montos habría mezclado el % real
        con un tipo de cambio adivinado. Leer el % del catálogo evita el
        problema por completo, porque un porcentaje no tiene moneda.

        Nota: esto solo cubre líneas cuya orden tiene audit_fee_id (el esquema
        de pago por % que usan MX/CR/CL); compras en otros esquemas (ej. precio
        fijo para US) no se toman en cuenta en la tasa por ahora.
        """
        if not template_ids:
            return {}

        domain = [
            ('product_id.product_tmpl_id', 'in', template_ids),
            ('service_start_date', '>=', date_from),
            ('service_start_date', '<=', date_to),
            ('order_id.state', '!=', 'cancel'),
            ('order_id.audit_fee_id', '!=', False),
        ]
        weighted = defaultdict(lambda: {'num': 0.0, 'den': 0.0})
        for line in self.env['purchase.order.line'].sudo().search(domain):
            order = line.order_id
            fee = order.partner_id.audit_fee_percentages_ids.filtered(
                lambda f: f.audit_fees_id == order.audit_fee_id)[:1]
            qty = line.product_qty or 0.0
            if not fee or not qty:
                continue

            tmpl_id = line.product_id.product_tmpl_id.id
            weighted[tmpl_id]['num'] += (fee.audit_percentage / 100.0) * qty
            weighted[tmpl_id]['den'] += qty

        return {
            tmpl_id: vals['num'] / vals['den']
            for tmpl_id, vals in weighted.items() if vals['den']
        }

    def _compute_and_set_provider_cost_rate(self):
        """Calcula y guarda provider_cost_rate para self, agrupando por
        presupuesto (para obtener el rango de temporada base una sola vez) y
        consultando el histórico de compras una sola vez por producto.

        Escribe en lote por cada valor de tasa distinto (en vez de línea por
        línea) para no disparar un write()/notificación de bus por cada
        registro cuando se generan cientos de líneas de golpe.
        """
        for budget in self.mapped('budget_id'):
            lines = self.filtered(lambda l: l.budget_id == budget)
            date_from = '{0}-09-01'.format(budget.year - 1)
            date_to = '{0}-08-31'.format(budget.year)
            rates = self._get_provider_cost_rates(lines.mapped('product_id').ids, date_from, date_to)
            by_rate = defaultdict(lambda: self.browse())
            for line in lines:
                by_rate[rates.get(line.product_id.id, 0.0)] |= line
            for rate, rate_lines in by_rate.items():
                rate_lines.write({'provider_cost_rate': rate})

    @api.onchange('product_id')
    def _onchange_product_id_provider_cost_rate(self):
        for rec in self:
            if rec.product_id and rec.budget_id:
                date_from = '{0}-09-01'.format(rec.budget_id.year - 1)
                date_to = '{0}-08-31'.format(rec.budget_id.year)
                rates = rec._get_provider_cost_rates([rec.product_id.id], date_from, date_to)
                rec.provider_cost_rate = rates.get(rec.product_id.id, 0.0)
            else:
                rec.provider_cost_rate = 0.0

    def _compute_and_set_operational_cost_rate(self):
        """Calcula y guarda operational_cost_rate para self, agrupando por
        presupuesto (para obtener rate_staff y rate_esquema una sola vez por
        presupuesto en vez de por línea) y escribiendo en lote por valor de
        tasa distinto, igual que _compute_and_set_provider_cost_rate.
        """
        for budget in self.mapped('budget_id'):
            lines = self.filtered(lambda l: l.budget_id == budget)
            rate_staff, rate_scheme = budget._get_operational_cost_rates()
            by_rate = defaultdict(lambda: self.browse())
            for line in lines:
                rate = rate_staff + rate_scheme.get(line.pao_sales_budget_scheme_id.id, 0.0)
                by_rate[rate] |= line
            for rate, rate_lines in by_rate.items():
                rate_lines.write({'operational_cost_rate': rate})

    @api.onchange('product_id')
    def _onchange_product_id_operational_cost_rate(self):
        for rec in self:
            if rec.product_id and rec.budget_id:
                rate_staff, rate_scheme = rec.budget_id._get_operational_cost_rates()
                rec.operational_cost_rate = rate_staff + rate_scheme.get(rec.pao_sales_budget_scheme_id.id, 0.0)
            else:
                rec.operational_cost_rate = 0.0


class PAOSalesBudgetActualLine(models.Model):
    _name = "pao.sales.budget.actual.line"
    _description = "PAO Annual Sales Budget Actual (Facturado) Lines"
    _order = "region_id, customer_category, customer_name, product_id_reference ASC"

    budget_id = fields.Many2one('pao.sales.budget', string='Budget', required=True, ondelete='cascade')
    region_id = fields.Many2one('crm.team', string='Region', ondelete='restrict')
    customer_category = fields.Selection([
        ('Clientes Clave', 'Clientes Clave'),
        ('Promotor', 'Promotor'),
        ('Clientes Individuales', 'Clientes Individuales'),
        ('Clientes Nuevos', 'Clientes Nuevos'),
    ], string='Customer Category')
    customer_name = fields.Char(string='Customer Name')
    product_id = fields.Many2one('product.template', string='Producto')
    currency_id = fields.Many2one(related='budget_id.currency_id')
    product_id_reference = fields.Char(related='product_id.default_code', store=True)
    pao_sales_budget_scheme_id = fields.Many2one(related='product_id.pao_sales_budget_scheme_id', store=True)
    price_unit = fields.Monetary(string='Average Price', currency_field='currency_id')
    # Quantity Month
    m01 = fields.Float("Jan", default=0.0)
    m02 = fields.Float("Feb", default=0.0)
    m03 = fields.Float("Mar", default=0.0)
    m04 = fields.Float("Apr", default=0.0)
    m05 = fields.Float("May", default=0.0)
    m06 = fields.Float("Jun", default=0.0)
    m07 = fields.Float("Jul", default=0.0)
    m08 = fields.Float("Aug", default=0.0)
    m09 = fields.Float("Sep", default=0.0)
    m10 = fields.Float("Oct", default=0.0)
    m11 = fields.Float("Nov", default=0.0)
    m12 = fields.Float("Dec", default=0.0)
    # Amount Month (igual que pao.sales.budget.line, necesario para el reporte por esquema)
    m01_amount = fields.Float("Total Amount Jan", compute='_compute_total_jan', store=True)
    m02_amount = fields.Float("Total Amount Feb", compute='_compute_total_feb', store=True)
    m03_amount = fields.Float("Total Amount Mar", compute='_compute_total_mar', store=True)
    m04_amount = fields.Float("Total Amount Apr", compute='_compute_total_apr', store=True)
    m05_amount = fields.Float("Total Amount May", compute='_compute_total_may', store=True)
    m06_amount = fields.Float("Total Amount Jun", compute='_compute_total_jun', store=True)
    m07_amount = fields.Float("Total Amount Jul", compute='_compute_total_jul', store=True)
    m08_amount = fields.Float("Total Amount Aug", compute='_compute_total_aug', store=True)
    m09_amount = fields.Float("Total Amount Sep", compute='_compute_total_sep', store=True)
    m10_amount = fields.Float("Total Amount Oct", compute='_compute_total_oct', store=True)
    m11_amount = fields.Float("Total Amount Nov", compute='_compute_total_nov', store=True)
    m12_amount = fields.Float("Total Amount Dec", compute='_compute_total_dec', store=True)

    total_quantity = fields.Float(string='Total Quantity', compute='_compute_total', store=True)
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total', currency_field='currency_id', store=True)

    @api.depends('m01','price_unit')
    def _compute_total_jan(self):
        for rec in self:
            rec.m01_amount = rec.m01 * (rec.price_unit or 0.0)
    @api.depends('m02','price_unit')
    def _compute_total_feb(self):
        for rec in self:
            rec.m02_amount = rec.m02 * (rec.price_unit or 0.0)
    @api.depends('m03','price_unit')
    def _compute_total_mar(self):
        for rec in self:
            rec.m03_amount = rec.m03 * (rec.price_unit or 0.0)
    @api.depends('m04','price_unit')
    def _compute_total_apr(self):
        for rec in self:
            rec.m04_amount = rec.m04 * (rec.price_unit or 0.0)
    @api.depends('m05','price_unit')
    def _compute_total_may(self):
        for rec in self:
            rec.m05_amount = rec.m05 * (rec.price_unit or 0.0)
    @api.depends('m06','price_unit')
    def _compute_total_jun(self):
        for rec in self:
            rec.m06_amount = rec.m06 * (rec.price_unit or 0.0)
    @api.depends('m07','price_unit')
    def _compute_total_jul(self):
        for rec in self:
            rec.m07_amount = rec.m07 * (rec.price_unit or 0.0)
    @api.depends('m08','price_unit')
    def _compute_total_aug(self):
        for rec in self:
            rec.m08_amount = rec.m08 * (rec.price_unit or 0.0)
    @api.depends('m09','price_unit')
    def _compute_total_sep(self):
        for rec in self:
            rec.m09_amount = rec.m09 * (rec.price_unit or 0.0)
    @api.depends('m10','price_unit')
    def _compute_total_oct(self):
        for rec in self:
            rec.m10_amount = rec.m10 * (rec.price_unit or 0.0)
    @api.depends('m11','price_unit')
    def _compute_total_nov(self):
        for rec in self:
            rec.m11_amount = rec.m11 * (rec.price_unit or 0.0)
    @api.depends('m12','price_unit')
    def _compute_total_dec(self):
        for rec in self:
            rec.m12_amount = rec.m12 * (rec.price_unit or 0.0)

    @api.depends('m01','m02','m03','m04','m05','m06','m07','m08','m09','m10','m11','m12','price_unit')
    def _compute_total(self):
        for rec in self:
            qty_sum = sum((rec.m01,rec.m02,rec.m03,rec.m04,rec.m05,rec.m06,rec.m07,rec.m08,rec.m09,rec.m10,rec.m11,rec.m12))
            rec.total_quantity = qty_sum
            rec.total_amount = qty_sum * (rec.price_unit or 0.0)


class PAOSalesBudgetVarianceReport(models.Model):
    _name = "pao.sales.budget.variance.report"
    _description = "PAO Sales Budget vs Actual Variance"
    _auto = False
    _order = "budget_id, region_id, customer_category, customer_name, product_id, month"

    id = fields.Integer(readonly=True)
    budget_id = fields.Many2one('pao.sales.budget', string='Budget', readonly=True)
    region_id = fields.Many2one('crm.team', string='Region', readonly=True)
    customer_category = fields.Selection([
        ('Clientes Clave', 'Clientes Clave'),
        ('Promotor', 'Promotor'),
        ('Clientes Individuales', 'Clientes Individuales'),
        ('Clientes Nuevos', 'Clientes Nuevos'),
    ], string='Customer Category', readonly=True)
    customer_name = fields.Char(string='Customer Name', readonly=True)
    product_id = fields.Many2one('product.template', string='Producto', readonly=True)
    month = fields.Selection([
        ('09', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dic'),
        ('01', 'Ene'), ('02', 'Feb'), ('03', 'Mar'), ('04', 'Abr'),
        ('05', 'May'), ('06', 'Jun'), ('07', 'Jul'), ('08', 'Ago'),
    ], string='Mes', readonly=True)
    budgeted_qty = fields.Float(string='Presupuestado', readonly=True)
    actual_qty = fields.Float(string='Real', readonly=True)
    variance_qty = fields.Float(string='Variación (Cant.)', readonly=True)
    variance_pct = fields.Float(string='Variación %', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        # month se guarda como texto ('01'..'12') porque los Selection de Odoo
        # requieren keys tipo string; con keys enteras, la reflexión de la
        # selección revienta al instalar el módulo (ir.model.fields.selection).
        budget_unpivot = "\n UNION ALL \n".join(
            "SELECT budget_id, region_id, customer_category, customer_name, product_id, "
            "'%(mm)s'::varchar AS month, m%(mm)s AS qty FROM pao_sales_budget_line" % {'mm': f'{m:02d}'}
            for m in range(1, 13)
        )
        actual_unpivot = "\n UNION ALL \n".join(
            "SELECT budget_id, region_id, customer_category, customer_name, product_id, "
            "'%(mm)s'::varchar AS month, m%(mm)s AS qty FROM pao_sales_budget_actual_line" % {'mm': f'{m:02d}'}
            for m in range(1, 13)
        )

        query = """
            CREATE OR REPLACE VIEW %(table)s AS (
                WITH budget_unpivot AS (
                    %(budget_unpivot)s
                ),
                actual_unpivot AS (
                    %(actual_unpivot)s
                )
                SELECT
                    row_number() OVER () AS id,
                    COALESCE(b.budget_id, a.budget_id) AS budget_id,
                    COALESCE(b.region_id, a.region_id) AS region_id,
                    COALESCE(b.customer_category, a.customer_category) AS customer_category,
                    COALESCE(b.customer_name, a.customer_name) AS customer_name,
                    COALESCE(b.product_id, a.product_id) AS product_id,
                    COALESCE(b.month, a.month) AS month,
                    COALESCE(b.qty, 0) AS budgeted_qty,
                    COALESCE(a.qty, 0) AS actual_qty,
                    (COALESCE(a.qty, 0) - COALESCE(b.qty, 0)) AS variance_qty,
                    CASE
                        WHEN COALESCE(b.qty, 0) = 0 AND COALESCE(a.qty, 0) > 0 THEN 9.999
                        WHEN COALESCE(b.qty, 0) = 0 THEN 0
                        ELSE ROUND(((COALESCE(a.qty, 0) - b.qty) / b.qty)::numeric, 4)
                    END AS variance_pct
                FROM budget_unpivot b
                FULL OUTER JOIN actual_unpivot a
                    ON b.budget_id = a.budget_id
                    AND b.region_id = a.region_id
                    AND b.customer_category = a.customer_category
                    AND b.customer_name = a.customer_name
                    AND b.product_id = a.product_id
                    AND b.month = a.month
            )
        """ % {
            'table': self._table,
            'budget_unpivot': budget_unpivot,
            'actual_unpivot': actual_unpivot,
        }
        self.env.cr.execute(query)

