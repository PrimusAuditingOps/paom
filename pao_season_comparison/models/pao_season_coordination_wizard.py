import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from . import billing_report as br
from . import coordination_report as cr


class PAOSeasonCoordinationWizard(models.TransientModel):
    _name = 'pao.season.coordination.wizard'
    _description = 'PAO Comparativo de Coordinación por Temporada'

    year_a = fields.Integer(string='Temporada base (año de inicio)', required=True,
                            default=lambda self: self._current_season_year() - 1)
    year_b = fields.Integer(string='Temporada a comparar (año de inicio)', required=True,
                            default=lambda self: self._current_season_year())
    season_a_range = fields.Char(string='Periodo base', compute='_compute_ranges')
    season_b_range = fields.Char(string='Periodo a comparar', compute='_compute_ranges')
    scheme_ids = fields.Many2many('pao.sales.budget.scheme', string='Esquemas',
                                  help='Vacío = todos los esquemas.')
    coordinator_ids = fields.Many2many('res.users', string='Coordinadores',
                                       help='Vacío = todos los coordinadores.')
    report_html = fields.Html(string='Reporte', readonly=True, sanitize=False)

    # ------------------------------------------------------------------
    # Temporadas
    # ------------------------------------------------------------------

    @api.model
    def _current_season_year(self):
        today = fields.Date.context_today(self)
        return today.year if today.month >= 9 else today.year - 1

    @api.model
    def _range_text(self, year):
        if not year or not (1990 <= year <= 2100):
            return False
        d1, d2 = br.season_dates(year)
        return '%s: del %s al %s' % (br.season_label(year), d1.strftime('%d/%m/%Y'), d2.strftime('%d/%m/%Y'))

    @api.depends('year_a', 'year_b')
    def _compute_ranges(self):
        for wiz in self:
            wiz.season_a_range = wiz._range_text(wiz.year_a)
            wiz.season_b_range = wiz._range_text(wiz.year_b)

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
    # Datos: servicios coordinados (líneas de compra)
    # ------------------------------------------------------------------

    def _get_base(self):
        """Un registro por (coordinador, esquema, cliente) con la cantidad
        ordenada por mes en cada temporada.

        Sale de purchase.report (el reporte de compras nativo, con sus
        extensiones de PAO: pao_customer_purchase_report y
        pao_purchase_report_agenda) y su qty_ordered, filtrando: compra no
        cancelada, estatus de auditoría 'Confirmada', producto comisionable y
        pedido de venta ligado (pao_customer_id, el cliente de ese pedido). La
        temporada y el mes los define service_start_date; el coordinador es
        coordinator_id y el esquema el del producto.

        purchase.report es un reporte dinámico (_table_query, depende de las
        empresas activas), por eso se usa como subconsulta y no como tabla.
        """
        self.ensure_one()
        self._check_years()
        a_from, a_to = br.season_dates(self.year_a)
        b_from, b_to = br.season_dates(self.year_b)
        params = {
            'a_from': a_from, 'a_to': a_to, 'b_from': b_from, 'b_to': b_to,
            'company_ids': tuple(self.env.companies.ids),
        }
        extra = ''
        if self.scheme_ids:
            extra += ' AND pt.pao_sales_budget_scheme_id IN %(scheme_ids)s'
            params['scheme_ids'] = tuple(self.scheme_ids.ids)
        if self.coordinator_ids:
            extra += ' AND r.coordinator_id IN %(coordinator_ids)s'
            params['coordinator_ids'] = tuple(self.coordinator_ids.ids)

        # El texto del subquery no lleva parámetros; se escapa cualquier '%'
        # literal para que execute() no lo confunda con un placeholder.
        report_query = self.env['purchase.report']._table_query.replace('%', '%%')
        query = """
            SELECT r.coordinator_id,
                   pt.pao_sales_budget_scheme_id,
                   r.pao_customer_id,
                   CASE WHEN r.service_start_date BETWEEN %(a_from)s AND %(a_to)s THEN 'a' ELSE 'b' END,
                   EXTRACT(MONTH FROM r.service_start_date)::int,
                   COALESCE(SUM(r.qty_ordered), 0)
              FROM ({report_query}) r
              JOIN product_template pt ON pt.id = r.product_tmpl_id
              JOIN auditconfirmation_auditstate st ON st.id = r.ac_audit_status
             WHERE r.state != 'cancel'
               AND r.pao_customer_id IS NOT NULL
               AND st.name IN ('Confirmada', 'Confirmed')
               AND pt.can_be_commissionable IS TRUE
               AND r.company_id IN %(company_ids)s
               AND (r.service_start_date BETWEEN %(a_from)s AND %(a_to)s
                    OR r.service_start_date BETWEEN %(b_from)s AND %(b_to)s)
               {extra}
          GROUP BY 1, 2, 3, 4, 5
        """.format(report_query=report_query, extra=extra)

        self.env.flush_all()
        self.env.cr.execute(query, params)

        data = {}
        for coord_id, scheme_id, partner_id, season, month, qty in self.env.cr.fetchall():
            months = data.setdefault((coord_id or False, scheme_id or False, partner_id),
                                     {m: [0.0, 0.0] for m in br.MONTHS_ORDER})
            months['%02d' % month][0 if season == 'a' else 1] += float(qty)

        partners = self.env['res.partner'].sudo().browse({key[2] for key in data})
        partner_by_id = {p.id: p for p in partners}
        users = self.env['res.users'].sudo().browse({key[0] for key in data if key[0]})
        coord_name = {u.id: u.name for u in users}
        schemes = self.env['pao.sales.budget.scheme'].sudo().browse({key[1] for key in data if key[1]})
        scheme_name = {s.id: s.name for s in schemes}
        scheme_seq = {s.id: s.sequence for s in schemes}

        base = []
        for (coord_id, scheme_id, partner_id), months in data.items():
            partner = partner_by_id[partner_id]
            base.append({
                'coord_id': coord_id,
                'coord_name': coord_name.get(coord_id) or _('Sin coordinador'),
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
                'months': months,
            })
        return base

    # ------------------------------------------------------------------
    # Reporte en pantalla
    # ------------------------------------------------------------------

    def action_generate_report(self):
        self.ensure_one()
        self.report_html = cr.render_html(self._get_base(), self.year_a, self.year_b)
        return True

    # ------------------------------------------------------------------
    # Excel
    # ------------------------------------------------------------------

    def action_export_excel(self):
        self.ensure_one()
        xlsx_data = cr.render_xlsx(self._get_base(), self.year_a, self.year_b)
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Comparativo_Coordinacion_%s_vs_%s.xlsx' % (
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
