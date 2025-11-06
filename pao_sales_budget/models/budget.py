from collections import defaultdict
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError
from logging import getLogger

_logger = getLogger(__name__)

class PAOSalesBudget(models.Model):
    _name = "pao.sales.budget"
    _description = "PAO Annual Sales Budget"


    name = fields.Char(required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',copy=False, string='Currency', default=2, required=True)
    year = fields.Integer(string='Año', required=True, copy=False, default=lambda self: fields.Date.context_today(self).year)
    line_ids = fields.One2many('pao.sales.budget.line', 'budget_id', string='Lines', copy=False)


    def action_view_budget_line(self):
        self.ensure_one()
        action = {
            'res_model': 'pao.sales.budget.line',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,pivot',
            'name': _("Budget Lines"),
            'target': 'current',  
            'context': {'group_by': ['region_id', 'customer_category', 'customer_name'], 'default_budget_id': self.id } ,
            'domain': [('budget_id', '=', self.id)],
        }
        return action

    def generate_budget_action(self):
        self.ensure_one()
        customer_category = ["Clientes Clave", "Promotor", "Clientes Individuales", "Clientes Nuevos"]
        team = self.env["crm.team"].search([("pao_include_in_budget","=",True)])
        date_from = '{0}-09-01'.format(self.year-1)
        date_to = '{0}-08-31'.format(self.year) 
        for region in team:
            for customer_type in customer_category:
                if customer_type == "Clientes Clave":
                    groups = self.env["customergroups.group"].search([("pao_include_in_budget","=",True)])
                    for group in groups:
                        domain = [('move_id.state', '=', 'posted'),
                            ('move_id.move_type', '=', 'out_invoice'),  
                            ('move_id.invoice_date', '>=', date_from),
                            ('move_id.invoice_date', '<=', date_to),
                            ("product_id.can_be_commissionable", "=", True),
                            ("move_id.partner_id.cgg_group_id", "=", group.id),
                            ("move_id.partner_id.team_id", "=", region.id)
                        ]
                        self.create_budget_line(domain,region,customer_type,group.name,"simple")
                elif customer_type == "Promotor":
                    promotors = self.env["comisionpromotores.promotor"].search([("pao_include_in_budget","=",True)])
                    for promotor in promotors:
                        domain = [('move_id.state', '=', 'posted'),
                            ('move_id.move_type', '=', 'out_invoice'),  
                            ('move_id.invoice_date', '>=', date_from),
                            ('move_id.invoice_date', '<=', date_to),
                            ("product_id.can_be_commissionable", "=", True),
                            ("move_id.partner_id.promotor_id", "=", promotor.id),
                            ("move_id.partner_id.team_id", "=", region.id)
                        ]
                        self.create_budget_line(domain,region,customer_type,promotor.name,"simple")
                elif customer_type == "Clientes Individuales":
                    domain = [
                        ('move_id.state', '=', 'posted'),
                        ('move_id.move_type', '=', 'out_invoice'),
                        ('move_id.invoice_date', '>=', date_from),
                        ('move_id.invoice_date', '<=', date_to),
                        ('product_id.can_be_commissionable', '=', True),
                        ('move_id.partner_id.team_id', '=', region.id),
                        '|',
                            ('move_id.partner_id.promotor_id', '=', False),
                            ('move_id.partner_id.promotor_id.pao_include_in_budget', '=', False),
                        '|',
                            ('move_id.partner_id.cgg_group_id', '=', False),
                            ('move_id.partner_id.cgg_group_id.pao_include_in_budget', '=', False)
                    ]
                    self.create_budget_line(domain,region,customer_type,"Clientes Ind.","simple")
                else:
                    budget_line = self.env['pao.sales.budget.line'].search([("region_id","=",region.id),("customer_category","=","Clientes Individuales")])
                    to_create = []
                    for line in budget_line:
                        line_vals = {
                            'budget_id': self.id,
                            'region_id': line.region_id.id,
                            'customer_category': customer_type,
                            'customer_name': customer_type,
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
            
        return {'message': _('Se han creado las líneas de presupuesto')}
    
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
            product = ln.product_id

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

        
class PAOSalesBudgetLine(models.Model):
    _name = "pao.sales.budget.line"
    _description = "PAO Annual Sales Budget Lines"
    _order = "region_id, customer_category, customer_name, product_id_reference ASC"

    budget_id = fields.Many2one('pao.sales.budget', string='Budget', required=True, ondelete='cascade')
    region_id = fields.Many2one('crm.team', string='Region',ondelete='restrict',)
    customer_category = fields.Char(string='Customer Category')
    customer_name = fields.Char(string='Customer Name')
    product_id = fields.Many2one('product.product', string='Producto')
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
    m01_amount = fields.Float("Total Amount Jan", compute='_compute_total_jan', currency_field='currency_id', store=True)
    m02_amount = fields.Float("Total Amount Feb", compute='_compute_total_feb', currency_field='currency_id', store=True)
    m03_amount = fields.Float("Total Amount Mar", compute='_compute_total_mar', currency_field='currency_id', store=True)
    m04_amount = fields.Float("Total Amount Apr", compute='_compute_total_apr', currency_field='currency_id', store=True)
    m05_amount = fields.Float("Total Amount May", compute='_compute_total_may', currency_field='currency_id', store=True)
    m06_amount = fields.Float("Total Amount Jun", compute='_compute_total_jun', currency_field='currency_id', store=True)
    m07_amount = fields.Float("Total Amount Jul", compute='_compute_total_jul', currency_field='currency_id', store=True)
    m08_amount = fields.Float("Total Amount Aug", compute='_compute_total_aug', currency_field='currency_id', store=True)
    m09_amount = fields.Float("Total Amount Sep", compute='_compute_total_sep', currency_field='currency_id', store=True)
    m10_amount = fields.Float("Total Amount Oct", compute='_compute_total_oct', currency_field='currency_id', store=True)
    m11_amount = fields.Float("Total Amount Nov", compute='_compute_total_nov', currency_field='currency_id', store=True)
    m12_amount = fields.Float("Total Amount Dec", compute='_compute_total_dec', currency_field='currency_id', store=True)


    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total', currency_field='currency_id', store=True)
    total_quantity = fields.Float(string='Total Quantity', compute='_compute_total', store=True)


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

