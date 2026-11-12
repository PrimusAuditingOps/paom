import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from . import billing_report as br


class PAOSeasonBillingWizard(models.TransientModel):
    _name = 'pao.season.billing.wizard'
    _description = 'PAO Comparativo de Facturación por Temporada'

    year_a = fields.Integer(string='Temporada base (año de inicio)', required=True,
                            default=lambda self: self._current_season_year() - 1)
    year_b = fields.Integer(string='Temporada a comparar (año de inicio)', required=True,
                            default=lambda self: self._current_season_year())
    cutoff_month = fields.Selection(
        br.MONTHS, string='Mes de corte',
        help='Opcional. Si eliges un mes, las dos temporadas se comparan de septiembre hasta ese mes '
             '(útil cuando la temporada actual sigue en curso). Vacío = toda la temporada.')
    season_a_range = fields.Char(string='Periodo base', compute='_compute_ranges')
    season_b_range = fields.Char(string='Periodo a comparar', compute='_compute_ranges')
    scheme_ids = fields.Many2many('pao.sales.budget.scheme', string='Esquemas',
                                  help='Vacío = todos los esquemas.')
    region_ids = fields.Many2many('crm.team', string='Regiones',
                                  help='Región del cliente. Vacío = todas.')
    group_ids = fields.Many2many('customergroups.group', 'pao_season_bill_group_rel', string='Grupos',
                                 help='Grupo del cliente. Vacío = todos.')
    promotor_ids = fields.Many2many('comisionpromotores.promotor', 'pao_season_bill_promotor_rel', string='Promotores',
                                    help='Promotor del cliente. Vacío = todos.')
    omit_no_scheme = fields.Boolean(
        string='Omitir productos sin esquema',
        help='Si está marcado, no se consideran los productos que no tienen esquema '
             'y no aparece el esquema "Sin esquema".')
    report_html = fields.Html(string='Reporte', readonly=True, sanitize=False)

    # ------------------------------------------------------------------
    # Temporadas
    # ------------------------------------------------------------------

    @api.model
    def _current_season_year(self):
        today = fields.Date.context_today(self)
        return today.year if today.month >= 9 else today.year - 1

    @api.model
    def _range_text(self, year, cutoff=None):
        if not year or not (1990 <= year <= 2100):
            return False
        d1, d2 = br.season_dates(year, cutoff)
        return '%s: del %s al %s' % (br.season_label(year), d1.strftime('%d/%m/%Y'), d2.strftime('%d/%m/%Y'))

    @api.depends('year_a', 'year_b', 'cutoff_month')
    def _compute_ranges(self):
        for wiz in self:
            wiz.season_a_range = wiz._range_text(wiz.year_a, wiz.cutoff_month)
            wiz.season_b_range = wiz._range_text(wiz.year_b, wiz.cutoff_month)

    @api.onchange('year_a')
    def _onchange_year_a(self):
        if self.year_a:
            self.year_b = self.year_a + 1

    def _check_years(self):
        self.ensure_one()
        for year in (self.year_a, self.year_b):
            if not (1990 <= (year or 0) <= 2100):
                raise UserError(_('Escribe el año de inicio de la temporada con 4 dígitos, por ejemplo 2025.'))
        if self.year_a == self.year_b:
            raise UserError(_('Elige dos temporadas distintas para compararlas.'))

    # ------------------------------------------------------------------
    # Datos: lo facturado (sales.invoicing.report) por esquema y cliente
    # ------------------------------------------------------------------

    def _get_rows(self):
        """Una fila por (esquema, cliente) que haya facturado algo en cualquiera
        de las dos temporadas, con cantidad y USD sin impuestos por mes.

        Lee de sales.invoicing.report (ya resta notas de crédito y devoluciones)
        solo productos con el flag de comisionable. La temporada se decide por
        invoice_date. El esquema sale del producto (pao_sales_budget_scheme_id)
        y el cliente es partner_id.
        """
        self.ensure_one()
        self._check_years()
        a_from, a_to = br.season_dates(self.year_a, self.cutoff_month)
        b_from, b_to = br.season_dates(self.year_b, self.cutoff_month)
        params = {
            'a_from': a_from, 'a_to': a_to, 'b_from': b_from, 'b_to': b_to,
            'company_ids': tuple(self.env.companies.ids),
        }
        extra = ''
        if self.scheme_ids:
            extra += ' AND pt.pao_sales_budget_scheme_id IN %(scheme_ids)s'
            params['scheme_ids'] = tuple(self.scheme_ids.ids)
        if self.region_ids:
            extra += ' AND rp.team_id IN %(team_ids)s'
            params['team_ids'] = tuple(self.region_ids.ids)
        if self.group_ids:
            extra += ' AND rp.cgg_group_id IN %(group_ids)s'
            params['group_ids'] = tuple(self.group_ids.ids)
        if self.promotor_ids:
            extra += ' AND rp.promotor_id IN %(promotor_ids)s'
            params['promotor_ids'] = tuple(self.promotor_ids.ids)
        if self.omit_no_scheme:
            extra += ' AND pt.pao_sales_budget_scheme_id IS NOT NULL'

        query = """
            SELECT sir.partner_id,
                   pt.pao_sales_budget_scheme_id,
                   CASE WHEN sir.invoice_date BETWEEN %(a_from)s AND %(a_to)s THEN 'a' ELSE 'b' END,
                   EXTRACT(MONTH FROM sir.invoice_date)::int,
                   COALESCE(SUM(sir.quantity), 0),
                   COALESCE(SUM(sir.usd_untaxed_total), 0)
              FROM {table} sir
              JOIN product_template pt ON pt.id = sir.product_tmpl_id
              JOIN res_partner rp ON rp.id = sir.partner_id
             WHERE pt.can_be_commissionable IS TRUE
               AND sir.company_id IN %(company_ids)s
               AND (sir.invoice_date BETWEEN %(a_from)s AND %(a_to)s
                    OR sir.invoice_date BETWEEN %(b_from)s AND %(b_to)s)
               {extra}
          GROUP BY 1, 2, 3, 4
        """.format(table=self.env['sales.invoicing.report']._table, extra=extra)

        self.env.flush_all()
        self.env.cr.execute(query, params)

        data = {}
        for partner_id, scheme_id, season, month, qty, amount in self.env.cr.fetchall():
            months = data.setdefault((scheme_id or False, partner_id),
                                     {m: [0.0, 0.0, 0.0, 0.0] for m in br.MONTHS_ORDER})
            cell = months['%02d' % month]
            offset = 0 if season == 'a' else 2
            cell[offset] += float(qty)
            cell[offset + 1] += float(amount)

        partners = self.env['res.partner'].sudo().browse({key[1] for key in data})
        partner_by_id = {p.id: p for p in partners}
        schemes = self.env['pao.sales.budget.scheme'].sudo().browse({key[0] for key in data if key[0]})
        scheme_name = {s.id: s.name for s in schemes}
        scheme_seq = {s.id: s.sequence for s in schemes}

        rows = []
        for (scheme_id, partner_id), months in data.items():
            qty_a = sum(c[0] for c in months.values())
            amt_a = sum(c[1] for c in months.values())
            qty_b = sum(c[2] for c in months.values())
            amt_b = sum(c[3] for c in months.values())
            status = br.status_of(qty_a, amt_a, qty_b, amt_b)
            if not status:
                continue
            partner = partner_by_id[partner_id]
            rows.append({
                'scheme_id': scheme_id,
                'scheme_name': scheme_name.get(scheme_id) or _('Sin esquema'),
                'scheme_seq': scheme_seq.get(scheme_id, 0),
                'partner_id': partner_id,
                'partner_name': partner.name or '',
                'group_id': partner.cgg_group_id.id,
                'group_name': partner.cgg_group_id.name or '',
                'promotor_id': partner.promotor_id.id,
                'promotor_name': partner.promotor_id.name or '',
                'region_id': partner.team_id.id,
                'region_name': partner.team_id.name or '',
                'months': months,
                'qty_a': qty_a, 'amt_a': amt_a, 'qty_b': qty_b, 'amt_b': amt_b,
                'status': status,
            })
        # Esquemas en el orden (sequence) del catálogo, "Sin esquema" al final;
        # dentro de cada esquema, clientes por nombre.
        rows.sort(key=lambda r: (not r['scheme_id'], r['scheme_seq'], r['scheme_name'].lower(), r['partner_name'].lower()))
        return rows

    # ------------------------------------------------------------------
    # Reporte en pantalla
    # ------------------------------------------------------------------

    def action_generate_report(self):
        self.ensure_one()
        self.report_html = br.render_html(self._get_rows(), self.year_a, self.year_b, self.cutoff_month)
        return True

    # ------------------------------------------------------------------
    # Excel
    # ------------------------------------------------------------------

    def action_export_excel(self):
        self.ensure_one()
        xlsx_data = br.render_xlsx(self._get_rows(), self.year_a, self.year_b, self.cutoff_month)
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Comparativo_Facturacion_%s_vs_%s.xlsx' % (
                br.season_label(self.year_a), br.season_label(self.year_b)),
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
