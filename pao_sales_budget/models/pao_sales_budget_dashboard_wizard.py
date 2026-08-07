import base64
import io
from collections import defaultdict

from odoo import models, fields, api, _


class PAOSalesBudgetDashboardWizard(models.TransientModel):
    _name = 'pao.sales.budget.dashboard.wizard'
    _description = 'PAO Sales Budget - Dashboard (Equipo de Ventas / Esquema)'

    MONTH_SELECTION = [
        ('09', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dic'),
        ('01', 'Ene'), ('02', 'Feb'), ('03', 'Mar'), ('04', 'Abr'),
        ('05', 'May'), ('06', 'Jun'), ('07', 'Jul'), ('08', 'Ago'),
    ]
    MONTHS_ORDER = [m[0] for m in MONTH_SELECTION]

    budget_id = fields.Many2one('pao.sales.budget', string='Presupuesto', required=True)
    report_html = fields.Html(string='Reporte', readonly=True, sanitize=False)

    # ------------------------------------------------------------------
    # Agregación
    # ------------------------------------------------------------------

    def _grouped_totals(self, groupby_field):
        """Agrupa pao.sales.budget.line de este presupuesto por groupby_field,
        sumando cantidad y monto de cada mes. Regresa una lista de dicts:
        [{'name': ..., 'qty': {mm: val}, 'amount': {mm: val}}, ...]
        """
        self.ensure_one()
        Line = self.env['pao.sales.budget.line'].sudo()
        month_fields = ['m%s' % m for m in self.MONTHS_ORDER]
        amount_fields = ['m%s_amount' % m for m in self.MONTHS_ORDER]

        groups = Line.read_group(
            [('budget_id', '=', self.budget_id.id)],
            fields=[f + ':sum' for f in month_fields + amount_fields],
            groupby=[groupby_field],
        )

        rows = []
        for g in groups:
            val = g[groupby_field]
            name = val[1] if val else _('Sin asignar')
            rows.append({
                'name': name,
                'qty': {m: g['m%s' % m] or 0.0 for m in self.MONTHS_ORDER},
                'amount': {m: g['m%s_amount' % m] or 0.0 for m in self.MONTHS_ORDER},
            })
        rows.sort(key=lambda r: r['name'])
        return rows

    def _get_team_data(self):
        return self._grouped_totals('region_id')

    def _get_scheme_data(self):
        return self._grouped_totals('pao_sales_budget_scheme_id')

    @api.model
    def _row_total_qty(self, row):
        return sum(row['qty'].values())

    @api.model
    def _row_total_amount(self, row):
        return sum(row['amount'].values())

    # ------------------------------------------------------------------
    # HTML (vista en pantalla)
    # ------------------------------------------------------------------

    def _render_table(self, title, first_col_label, rows, header_class):
        def fmt(v):
            return '{:,.2f}'.format(v)

        month_headers = ''.join(
            '<th colspan="2">%s</th>' % label for _mm, label in self.MONTH_SELECTION
        )
        month_subheaders = ''.join(
            '<th>Cant.</th><th>Monto</th>' for _mm in self.MONTHS_ORDER
        )

        body_rows = ''
        total_qty_all = defaultdict(float)
        total_amount_all = defaultdict(float)
        for row in rows:
            cells = ''
            for m in self.MONTHS_ORDER:
                cells += '<td>%s</td><td>%s</td>' % (fmt(row['qty'][m]), fmt(row['amount'][m]))
                total_qty_all[m] += row['qty'][m]
                total_amount_all[m] += row['amount'][m]
            body_rows += '<tr><td>%s</td>%s<td>%s</td><td>%s</td></tr>' % (
                row['name'], cells, fmt(self._row_total_qty(row)), fmt(self._row_total_amount(row))
            )

        total_cells = ''
        grand_qty = grand_amount = 0.0
        for m in self.MONTHS_ORDER:
            total_cells += '<td>%s</td><td>%s</td>' % (fmt(total_qty_all[m]), fmt(total_amount_all[m]))
            grand_qty += total_qty_all[m]
            grand_amount += total_amount_all[m]
        total_row = '<tr class="ns-total-row"><td>%s</td>%s<td>%s</td><td>%s</td></tr>' % (
            _('Total / General'), total_cells, fmt(grand_qty), fmt(grand_amount)
        )

        return '''
        <div class="ns-report-block">
          <div class="ns-report-title %s">%s</div>
          <table class="ns-report-table">
            <thead>
              <tr>
                <th rowspan="2">%s</th>
                %s
                <th colspan="2">Total</th>
              </tr>
              <tr>
                %s
                <th>Cant.</th><th>Monto</th>
              </tr>
            </thead>
            <tbody>
              %s
              %s
            </tbody>
          </table>
        </div>
        ''' % (header_class, title, first_col_label, month_headers, month_subheaders, body_rows, total_row)

    def action_generate_report(self):
        self.ensure_one()
        rows_team = self._get_team_data()
        rows_scheme = self._get_scheme_data()

        style = '''<style>
            .ns-report-block{margin-bottom:24px;overflow-x:auto;}
            .ns-report-title{padding:6px 10px;color:white;font-weight:bold;font-size:13px;}
            .ns-title-team{background:#C0006E;}
            .ns-title-scheme{background:#2E7D32;}
            .ns-report-table{border-collapse:collapse;width:100%;font-size:12px;}
            .ns-report-table th, .ns-report-table td{border:1px solid #ddd;padding:4px 8px;text-align:right;white-space:nowrap;}
            .ns-report-table th{background:#f5f5f5;text-align:center;}
            .ns-report-table td:first-child, .ns-report-table th:first-child{text-align:left;}
            .ns-total-row td{font-weight:bold;border-top:2px solid #333;}
        </style>'''

        table_team = self._render_table(_('Presupuesto por Equipo de Ventas'), _('Equipo de Ventas'), rows_team, 'ns-title-team')
        table_scheme = self._render_table(_('Presupuesto por Esquema'), _('Esquema'), rows_scheme, 'ns-title-scheme')

        self.report_html = style + table_team + table_scheme
        return True

    # ------------------------------------------------------------------
    # Excel
    # ------------------------------------------------------------------

    def action_export_excel(self):
        self.ensure_one()
        from odoo.tools.misc import xlsxwriter

        rows_team = self._get_team_data()
        rows_scheme = self._get_scheme_data()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        fmts = {
            'header_team': workbook.add_format({'bold': True, 'bg_color': '#C0006E', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'}),
            'header_scheme': workbook.add_format({'bold': True, 'bg_color': '#2E7D32', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'}),
            'sub_header': workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1, 'align': 'center'}),
            'label': workbook.add_format({'border': 1}),
            'label_total': workbook.add_format({'border': 1, 'bold': True}),
            'num': workbook.add_format({'border': 1, 'num_format': '#,##0.00'}),
            'num_total': workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'bold': True}),
        }

        def write_sheet(sheet_name, first_col_label, rows, header_fmt):
            ws = workbook.add_worksheet(sheet_name)
            ws.merge_range(0, 0, 1, 0, first_col_label, header_fmt)
            col = 1
            for _mm, label in self.MONTH_SELECTION:
                ws.merge_range(0, col, 0, col + 1, label, header_fmt)
                ws.write(1, col, 'Cant.', fmts['sub_header'])
                ws.write(1, col + 1, 'Monto', fmts['sub_header'])
                col += 2
            ws.merge_range(0, col, 0, col + 1, 'Total', header_fmt)
            ws.write(1, col, 'Cant.', fmts['sub_header'])
            ws.write(1, col + 1, 'Monto', fmts['sub_header'])
            total_col = col

            ws.set_column(0, 0, 24)
            ws.set_column(1, total_col + 1, 11)
            ws.freeze_panes(2, 1)

            row = 2
            total_qty_all = defaultdict(float)
            total_amount_all = defaultdict(float)
            for r in rows:
                ws.write(row, 0, r['name'], fmts['label'])
                col = 1
                for m in self.MONTHS_ORDER:
                    ws.write(row, col, r['qty'][m], fmts['num'])
                    ws.write(row, col + 1, r['amount'][m], fmts['num'])
                    total_qty_all[m] += r['qty'][m]
                    total_amount_all[m] += r['amount'][m]
                    col += 2
                ws.write(row, total_col, self._row_total_qty(r), fmts['num'])
                ws.write(row, total_col + 1, self._row_total_amount(r), fmts['num'])
                row += 1

            ws.write(row, 0, _('Total / General'), fmts['label_total'])
            col = 1
            grand_qty = grand_amount = 0.0
            for m in self.MONTHS_ORDER:
                ws.write(row, col, total_qty_all[m], fmts['num_total'])
                ws.write(row, col + 1, total_amount_all[m], fmts['num_total'])
                grand_qty += total_qty_all[m]
                grand_amount += total_amount_all[m]
                col += 2
            ws.write(row, total_col, grand_qty, fmts['num_total'])
            ws.write(row, total_col + 1, grand_amount, fmts['num_total'])

        write_sheet('Equipo de Ventas', 'Equipo de Ventas', rows_team, fmts['header_team'])
        write_sheet('Esquema', 'Esquema', rows_scheme, fmts['header_scheme'])

        workbook.close()
        xlsx_data = output.getvalue()

        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Dashboard_Presupuesto_%s.xlsx' % (self.budget_id.name or self.budget_id.id),
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
