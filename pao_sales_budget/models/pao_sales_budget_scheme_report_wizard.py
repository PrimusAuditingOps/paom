import base64
import io
from collections import defaultdict

from odoo import models, fields, api, _


class PAOSalesBudgetSchemeReportWizard(models.TransientModel):
    _name = 'pao.sales.budget.scheme.report.wizard'
    _description = 'PAO Sales Budget - Reporte por Esquema (Mes vs Acumulado)'

    MONTH_SELECTION = [
        ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
        ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
    ]
    MONTHS_ORDER = [m[0] for m in MONTH_SELECTION]

    budget_id = fields.Many2one('pao.sales.budget', string='Presupuesto', required=True)
    month = fields.Selection(MONTH_SELECTION, string='Mes de Corte', required=True,
                              default=lambda self: self._default_month())
    report_html = fields.Html(string='Reporte', readonly=True, sanitize=False)

    def _default_month(self):
        today = fields.Date.context_today(self)
        mm = '%02d' % today.month
        return mm if mm in self.MONTHS_ORDER else '09'

    # ------------------------------------------------------------------
    # Agregación
    # ------------------------------------------------------------------

    def _get_scheme_data(self):
        """Arma, por esquema, la comparación Objetivo (pao.sales.budget.line) vs
        Real (pao.sales.budget.actual.line) para el mes de corte seleccionado y
        para el acumulado Sep..mes de corte. Tres métricas por esquema:
        - # Facturado: cantidad total (todas las categorías de cliente).
        - $ Facturado: monto total (m0X_amount, ya calculado por línea).
        - # Clientes Nuevos: cantidad de las líneas de categoría "Clientes Nuevos"
          únicamente (en este negocio 1 unidad de producto = 1 cliente, por eso
          se reusa la misma cantidad en vez de contar partners distintos).
        """
        self.ensure_one()
        budget = self.budget_id
        Scheme = self.env['pao.sales.budget.scheme'].sudo()
        Line = self.env['pao.sales.budget.line'].sudo()
        Actual = self.env['pao.sales.budget.actual.line'].sudo()

        schemes = Scheme.search([
            '|', ('company_id', '=', False), ('company_id', '=', budget.company_id.id),
        ], order='name')

        month_fields = ['m%s' % m for m in self.MONTHS_ORDER]
        amount_fields = ['m%s_amount' % m for m in self.MONTHS_ORDER]

        def grouped_totals(Model, extra_domain, fields_list):
            groups = Model.read_group(
                [('budget_id', '=', budget.id)] + extra_domain,
                fields=[f + ':sum' for f in fields_list],
                groupby=['pao_sales_budget_scheme_id'],
            )
            result = defaultdict(lambda: {f: 0.0 for f in fields_list})
            for g in groups:
                scheme_val = g['pao_sales_budget_scheme_id']
                scheme_id = scheme_val[0] if scheme_val else False
                for f in fields_list:
                    result[scheme_id][f] = g[f] or 0.0
            return result

        all_fields = month_fields + amount_fields
        budget_totals = grouped_totals(Line, [], all_fields)
        actual_totals = grouped_totals(Actual, [], all_fields)
        budget_new = grouped_totals(Line, [('customer_category', '=', 'Clientes Nuevos')], month_fields)
        actual_new = grouped_totals(Actual, [('customer_category', '=', 'Clientes Nuevos')], month_fields)

        cutoff_idx = self.MONTHS_ORDER.index(self.month)
        cumulative_months = self.MONTHS_ORDER[:cutoff_idx + 1]

        def variance(obj, real):
            """Regresa (delta, fracción_var, sin_objetivo)."""
            if obj == 0:
                return (real - obj), (9.999 if real > 0 else 0.0), (real > 0)
            return (real - obj), ((real - obj) / obj), False

        def build_row(name, b, a, bn, an, month_keys):
            qty_o = sum(b['m%s' % m] for m in month_keys)
            qty_r = sum(a['m%s' % m] for m in month_keys)
            amt_o = sum(b['m%s_amount' % m] for m in month_keys)
            amt_r = sum(a['m%s_amount' % m] for m in month_keys)
            new_o = sum(bn['m%s' % m] for m in month_keys)
            new_r = sum(an['m%s' % m] for m in month_keys)
            return {
                'name': name,
                'qty': (qty_o, qty_r) + variance(qty_o, qty_r),
                'amount': (amt_o, amt_r) + variance(amt_o, amt_r),
                'new': (new_o, new_r) + variance(new_o, new_r),
            }

        def totals_row(rows):
            qty_o = sum(r['qty'][0] for r in rows)
            qty_r = sum(r['qty'][1] for r in rows)
            amt_o = sum(r['amount'][0] for r in rows)
            amt_r = sum(r['amount'][1] for r in rows)
            new_o = sum(r['new'][0] for r in rows)
            new_r = sum(r['new'][1] for r in rows)
            return {
                'name': _('Total / General'),
                'qty': (qty_o, qty_r) + variance(qty_o, qty_r),
                'amount': (amt_o, amt_r) + variance(amt_o, amt_r),
                'new': (new_o, new_r) + variance(new_o, new_r),
            }

        rows_mes, rows_acum = [], []
        for scheme in schemes:
            sid = scheme.id
            b, a = budget_totals[sid], actual_totals[sid]
            bn, an = budget_new[sid], actual_new[sid]
            rows_mes.append(build_row(scheme.name, b, a, bn, an, [self.month]))
            rows_acum.append(build_row(scheme.name, b, a, bn, an, cumulative_months))

        rows_mes.append(totals_row(rows_mes))
        rows_acum.append(totals_row(rows_acum))
        return rows_mes, rows_acum

    # ------------------------------------------------------------------
    # HTML (vista en pantalla)
    # ------------------------------------------------------------------

    def _bar_chart_svg(self, rows, metric_key, title):
        data_rows = [r for r in rows if r['name'] != _('Total / General')]
        if not data_rows:
            return ''
        values = [(r['name'], r[metric_key][0], r[metric_key][1]) for r in data_rows]
        max_val = max([max(o, real) for _, o, real in values] + [1]) or 1

        bar_w, gap, group_w = 16, 4, 56
        top_pad, bottom_pad, chart_h = 10, 34, 110
        height = top_pad + chart_h + bottom_pad
        width = max(220, group_w * len(values) + 40)

        bars, labels = '', ''
        for i, (name, o, real) in enumerate(values):
            x0 = 30 + i * group_w
            h_o = (o / max_val) * chart_h
            h_r = (real / max_val) * chart_h
            y_o = top_pad + chart_h - h_o
            y_r = top_pad + chart_h - h_r
            color_r = '#2e7d32' if real >= o else '#c62828'
            bars += '<rect x="%.1f" y="%.1f" width="%d" height="%.1f" fill="#B0BEC5"/>' % (x0, y_o, bar_w, h_o)
            bars += '<rect x="%.1f" y="%.1f" width="%d" height="%.1f" fill="%s"/>' % (
                x0 + bar_w + gap, y_r, bar_w, h_r, color_r)
            label = (name[:9] + '…') if len(name) > 10 else name
            labels += '<text x="%.1f" y="%d" font-size="9" text-anchor="middle">%s</text>' % (
                x0 + bar_w, top_pad + chart_h + 12, label)

        return '''
        <div class="ns-report-chart">
          <div class="ns-chart-title">%s</div>
          <svg width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">
            %s
            %s
            <line x1="20" y1="%d" x2="%d" y2="%d" stroke="#999"/>
          </svg>
          <div class="ns-chart-legend">
            <span class="ns-leg-box" style="background:#B0BEC5;"></span> Objetivo
            &nbsp; <span class="ns-leg-box" style="background:#2e7d32;"></span> Real (cumple)
            &nbsp; <span class="ns-leg-box" style="background:#c62828;"></span> Real (debajo)
          </div>
        </div>
        ''' % (title, width, height, bars, labels, top_pad + chart_h, width, top_pad + chart_h)

    def _render_table(self, title, rows, header_class):
        def fmt(v):
            return '{:,.2f}'.format(v)

        def fmt_pct(pct, unbudgeted):
            cls = 'ns-unbud' if unbudgeted else ('ns-neg' if pct < -0.0001 else ('ns-pos' if pct > 0.0001 else 'ns-ok'))
            return '<span class="ns-pct %s">%.0f%%</span>' % (cls, pct * 100)

        def metric_cells(metric):
            o, r, v, p, u = metric
            return '<td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (fmt(o), fmt(r), fmt(v), fmt_pct(p, u))

        body_rows = ''
        for row in rows:
            is_total = row['name'] == _('Total / General')
            tr_class = ' class="ns-total-row"' if is_total else ''
            body_rows += '<tr%s><td>%s</td>%s%s%s</tr>' % (
                tr_class, row['name'],
                metric_cells(row['qty']), metric_cells(row['amount']), metric_cells(row['new'])
            )

        return '''
        <div class="ns-report-block">
          <div class="ns-report-title %s">%s</div>
          <table class="ns-report-table">
            <thead>
              <tr>
                <th rowspan="2">Esquema</th>
                <th colspan="4"># Facturado</th>
                <th colspan="4">$ Facturado</th>
                <th colspan="4"># Clientes Nuevos</th>
              </tr>
              <tr>
                <th>Objetivo</th><th>Real</th><th>Var #</th><th>Var %%</th>
                <th>Objetivo</th><th>Real</th><th>Var #</th><th>Var %%</th>
                <th>Objetivo</th><th>Real</th><th>Var #</th><th>Var %%</th>
              </tr>
            </thead>
            <tbody>
              %s
            </tbody>
          </table>
        </div>
        ''' % (header_class, title, body_rows)

    def action_generate_report(self):
        self.ensure_one()
        rows_mes, rows_acum = self._get_scheme_data()
        month_label = dict(self.MONTH_SELECTION)[self.month]

        style = '''<style>
            .ns-report-block{margin-bottom:20px;}
            .ns-report-title{padding:6px 10px;color:white;font-weight:bold;font-size:13px;}
            .ns-title-mes{background:#C0006E;}
            .ns-title-acum{background:#2E7D32;}
            .ns-report-table{border-collapse:collapse;width:100%;font-size:12px;}
            .ns-report-table th, .ns-report-table td{border:1px solid #ddd;padding:4px 8px;text-align:right;}
            .ns-report-table th{background:#f5f5f5;text-align:center;}
            .ns-report-table td:first-child, .ns-report-table th:first-child{text-align:left;}
            .ns-total-row td{font-weight:bold;border-top:2px solid #333;}
            .ns-pct{padding:1px 5px;border-radius:3px;}
            .ns-pos{background:#FFEB9C;color:#9C6500;}
            .ns-neg{background:#FFC7CE;color:#9C0006;}
            .ns-ok{background:#C6EFCE;color:#006100;}
            .ns-unbud{background:#BDD7EE;color:#1F4E78;}
            .ns-report-chart{margin-bottom:8px;}
            .ns-chart-title{font-size:12px;font-weight:bold;margin-bottom:4px;}
            .ns-chart-legend{font-size:10px;color:#666;margin-top:2px;}
            .ns-leg-box{display:inline-block;width:9px;height:9px;}
        </style>'''

        chart_mes = self._bar_chart_svg(rows_mes, 'qty', '# Facturado — %s' % month_label)
        chart_acum = self._bar_chart_svg(rows_acum, 'qty', '# Facturado — Acumulado a %s' % month_label)
        table_mes = self._render_table(month_label, rows_mes, 'ns-title-mes')
        table_acum = self._render_table('Acumulado a %s' % month_label, rows_acum, 'ns-title-acum')

        self.report_html = style + chart_mes + table_mes + chart_acum + table_acum
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ------------------------------------------------------------------
    # Excel
    # ------------------------------------------------------------------

    def action_export_excel(self):
        self.ensure_one()
        from odoo.tools.misc import xlsxwriter

        rows_mes, rows_acum = self._get_scheme_data()
        month_label = dict(self.MONTH_SELECTION)[self.month]

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        fmts = {
            'header_mes': workbook.add_format({'bold': True, 'bg_color': '#C0006E', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'}),
            'header_acum': workbook.add_format({'bold': True, 'bg_color': '#2E7D32', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'}),
            'sub_header': workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1, 'align': 'center'}),
            'label': workbook.add_format({'border': 1}),
            'label_total': workbook.add_format({'border': 1, 'bold': True}),
            'num': workbook.add_format({'border': 1, 'num_format': '#,##0.00'}),
            'num_total': workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'bold': True}),
            'pct_ok': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#C6EFCE', 'font_color': '#006100'}),
            'pct_neg': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#FFC7CE', 'font_color': '#9C0006'}),
            'pct_pos': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#FFEB9C', 'font_color': '#9C6500'}),
            'pct_unbud': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#BDD7EE', 'font_color': '#1F4E78'}),
        }

        def pct_format(pct, unbudgeted, is_total):
            if unbudgeted:
                return fmts['pct_unbud']
            if pct < -0.0001:
                return fmts['pct_neg']
            elif pct > 0.0001:
                return fmts['pct_pos']
            return fmts['pct_ok']

        def write_sheet(name, title, rows, header_fmt):
            ws = workbook.add_worksheet(name)
            ws.merge_range(0, 0, 1, 0, 'Esquema', header_fmt)
            col = 1
            for group_title in ('# Facturado', '$ Facturado', '# Clientes Nuevos'):
                ws.merge_range(0, col, 0, col + 3, group_title, header_fmt)
                ws.write(1, col, 'Objetivo', fmts['sub_header'])
                ws.write(1, col + 1, 'Real', fmts['sub_header'])
                ws.write(1, col + 2, 'Var #', fmts['sub_header'])
                ws.write(1, col + 3, 'Var %', fmts['sub_header'])
                col += 4
            ws.set_column(0, 0, 22)
            ws.set_column(1, col - 1, 11)
            ws.freeze_panes(2, 1)

            row = 2
            for r in rows:
                is_total = r['name'] == _('Total / General')
                label_fmt = fmts['label_total'] if is_total else fmts['label']
                num_fmt = fmts['num_total'] if is_total else fmts['num']
                ws.write(row, 0, r['name'], label_fmt)
                col = 1
                for metric in ('qty', 'amount', 'new'):
                    o, real, v, p, u = r[metric]
                    ws.write(row, col, o, num_fmt)
                    ws.write(row, col + 1, real, num_fmt)
                    ws.write(row, col + 2, v, num_fmt)
                    ws.write(row, col + 3, p, pct_format(p, u, is_total))
                    col += 4
                row += 1

        write_sheet('Mes - %s' % month_label, month_label, rows_mes, fmts['header_mes'])
        write_sheet('Acumulado', 'Acumulado a %s' % month_label, rows_acum, fmts['header_acum'])

        workbook.close()
        xlsx_data = output.getvalue()

        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Reporte_Esquema_%s_%s.xlsx' % (self.budget_id.name or self.budget_id.id, month_label),
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
