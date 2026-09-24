import base64
import io
from collections import defaultdict

from odoo import models, fields, api, _


class PAOSalesBudgetDashboardWizard(models.TransientModel):
    _name = 'pao.sales.budget.dashboard.wizard'
    _description = 'PAO Sales Budget - Dashboard (Región / Esquema, Objetivo vs Real, por mes)'

    MONTH_SELECTION = [
        ('09', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dic'),
        ('01', 'Ene'), ('02', 'Feb'), ('03', 'Mar'), ('04', 'Abr'),
        ('05', 'May'), ('06', 'Jun'), ('07', 'Jul'), ('08', 'Ago'),
    ]
    MONTHS_ORDER = [m[0] for m in MONTH_SELECTION]

    budget_id = fields.Many2one('pao.sales.budget', string='Presupuesto', required=True)
    month = fields.Selection(
        [('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
         ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
         ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto')],
        string='Mes de Corte', required=True,
        default=lambda self: self._default_month())
    report_html = fields.Html(string='Reporte', readonly=True, sanitize=False)

    # ------------------------------------------------------------------
    # Agregación: Objetivo (pao.sales.budget.line) vs Real (pao.sales.budget.actual.line),
    # desglosado por mes.
    # ------------------------------------------------------------------

    def _budget_vs_actual_monthly(self, groupby_fields):
        """Regresa una lista de dicts, uno por combinación de valores de
        groupby_fields (p.ej. solo región, solo esquema, o región+categoría de
        cliente), con cantidad y monto de cada mes tanto de lo presupuestado
        como de lo realmente facturado. Usa unión de llaves presentes en
        cualquiera de los dos lados, para no perder registros que solo tengan
        real sin presupuesto o viceversa.
        """
        self.ensure_one()
        Line = self.env['pao.sales.budget.line'].sudo()
        Actual = self.env['pao.sales.budget.actual.line'].sudo()
        month_fields = ['m%s' % m for m in self.MONTHS_ORDER]
        amount_fields = ['m%s_amount' % m for m in self.MONTHS_ORDER]
        all_fields = month_fields + amount_fields
        zero_months = {m: 0.0 for m in self.MONTHS_ORDER}

        def key_and_name(g):
            key_parts, name_parts = [], []
            for f in groupby_fields:
                val = g[f]
                if isinstance(val, (list, tuple)):
                    key_parts.append(val[0])
                    name_parts.append(val[1])
                elif val:
                    key_parts.append(val)
                    name_parts.append(val)
                else:
                    key_parts.append(False)
                    name_parts.append(_('Sin asignar'))
            return tuple(key_parts), ' / '.join(name_parts)

        def grouped(Model):
            groups = Model.read_group(
                [('budget_id', '=', self.budget_id.id)],
                fields=[f + ':sum' for f in all_fields],
                groupby=groupby_fields,
                lazy=False,
            )
            result = {}
            for g in groups:
                key, name = key_and_name(g)
                result[key] = {
                    'name': name,
                    'qty': {m: g['m%s' % m] or 0.0 for m in self.MONTHS_ORDER},
                    'amount': {m: g['m%s_amount' % m] or 0.0 for m in self.MONTHS_ORDER},
                }
            return result

        budget = grouped(Line)
        actual = grouped(Actual)

        rows = []
        for key in set(budget.keys()) | set(actual.keys()):
            b = budget.get(key)
            a = actual.get(key)
            rows.append({
                'name': (b or a)['name'],
                'qty_budget': (b or {}).get('qty', zero_months),
                'qty_actual': (a or {}).get('qty', zero_months),
                'amount_budget': (b or {}).get('amount', zero_months),
                'amount_actual': (a or {}).get('amount', zero_months),
            })
        rows.sort(key=lambda r: r['name'])
        return rows

    @api.model
    def _variance(self, obj, real):
        """Regresa (delta, fracción_var, sin_objetivo)."""
        if obj == 0:
            return (real - obj), (9.999 if real > 0 else 0.0), (real > 0)
        return (real - obj), ((real - obj) / obj), False

    def _metric_monthly_rows(self, base_rows, metric):
        """base_rows viene de _budget_vs_actual_monthly. metric es 'qty' o 'amount'.
        Regresa filas listas para render: por cada equipo/esquema, Objetivo/Real/Var%
        de cada mes más un bloque de Total de temporada; y al final una fila de
        Total / General sumando todos los equipos/esquemas.
        """
        rows = []
        for r in base_rows:
            obj_by_month = r['%s_budget' % metric]
            real_by_month = r['%s_actual' % metric]
            months = {}
            for m in self.MONTHS_ORDER:
                o = obj_by_month[m]
                real = real_by_month[m]
                _delta, pct, unbudgeted = self._variance(o, real)
                months[m] = {'obj': o, 'real': real, 'pct': pct, 'unbudgeted': unbudgeted}
            total_o = sum(obj_by_month.values())
            total_r = sum(real_by_month.values())
            _delta, pct_t, unbud_t = self._variance(total_o, total_r)
            rows.append({
                'name': r['name'],
                'months': months,
                'total': {'obj': total_o, 'real': total_r, 'pct': pct_t, 'unbudgeted': unbud_t},
            })

        total_months = {}
        for m in self.MONTHS_ORDER:
            to = sum(r['months'][m]['obj'] for r in rows)
            tr = sum(r['months'][m]['real'] for r in rows)
            _delta, pct, unbudgeted = self._variance(to, tr)
            total_months[m] = {'obj': to, 'real': tr, 'pct': pct, 'unbudgeted': unbudgeted}
        grand_o = sum(r['total']['obj'] for r in rows)
        grand_r = sum(r['total']['real'] for r in rows)
        _delta, pct, unbudgeted = self._variance(grand_o, grand_r)
        rows.append({
            'name': _('Total / General'),
            'months': total_months,
            'total': {'obj': grand_o, 'real': grand_r, 'pct': pct, 'unbudgeted': unbudgeted},
            'is_total': True,
        })
        return rows

    def _get_team_data(self):
        return self._budget_vs_actual_monthly(['region_id'])

    def _get_scheme_data(self):
        return self._budget_vs_actual_monthly(['pao_sales_budget_scheme_id'])

    def _get_region_category_data(self):
        return self._budget_vs_actual_monthly(['customer_category', 'region_id'])

    def _default_month(self):
        mm = '%02d' % fields.Date.context_today(self).month
        return mm if mm in self.MONTHS_ORDER else '09'

    # ------------------------------------------------------------------
    # Reporte por Esquema con mes de corte (Mes vs Acumulado): Objetivo vs Real
    # de # Facturado, $ Facturado y # Clientes Nuevos.
    # ------------------------------------------------------------------

    def _get_scheme_cutoff_data(self):
        """Por esquema, compara Objetivo (pao.sales.budget.line) vs Real
        (pao.sales.budget.actual.line) para el mes de corte y para el
        acumulado Sep..mes de corte. Tres métricas por esquema:
        - # Facturado: cantidad total (todas las categorías de cliente).
        - $ Facturado: monto total (m0X_amount, ya calculado por línea).
        - # Clientes Nuevos: cantidad de las líneas de categoría "Clientes
          Nuevos" únicamente (1 unidad de producto = 1 cliente).
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

        def metric(o, real):
            delta, pct, unbudgeted = self._variance(o, real)
            return (o, real, delta, pct, unbudgeted)

        def build_row(name, b, a, bn, an, month_keys):
            return {
                'name': name,
                'qty': metric(sum(b['m%s' % m] for m in month_keys), sum(a['m%s' % m] for m in month_keys)),
                'amount': metric(sum(b['m%s_amount' % m] for m in month_keys), sum(a['m%s_amount' % m] for m in month_keys)),
                'new': metric(sum(bn['m%s' % m] for m in month_keys), sum(an['m%s' % m] for m in month_keys)),
            }

        def totals_row(rows):
            return {
                'name': _('Total / General'),
                'is_total': True,
                'qty': metric(sum(r['qty'][0] for r in rows), sum(r['qty'][1] for r in rows)),
                'amount': metric(sum(r['amount'][0] for r in rows), sum(r['amount'][1] for r in rows)),
                'new': metric(sum(r['new'][0] for r in rows), sum(r['new'][1] for r in rows)),
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

    def _bar_chart_svg(self, rows, metric_key, title):
        data_rows = [r for r in rows if not r.get('is_total')]
        if not data_rows:
            return ''
        values = [(r['name'], r[metric_key][0], r[metric_key][1]) for r in data_rows]
        max_val = max([max(o, real) for _n, o, real in values] + [1]) or 1

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

    def _render_cutoff_table(self, title, rows, header_class):
        def fmt(v):
            return '{:,.2f}'.format(v)

        def metric_cells(m):
            o, real, delta, pct, unbudgeted = m
            return '<td>%s</td><td>%s</td><td>%s</td><td><span class="ns-pct %s">%.0f%%</span></td>' % (
                fmt(o), fmt(real), fmt(delta), self._pct_class(pct, unbudgeted), pct * 100)

        body_rows = ''
        for row in rows:
            tr_class = ' class="ns-total-row"' if row.get('is_total') else ''
            body_rows += '<tr%s><td>%s</td>%s%s%s</tr>' % (
                tr_class, row['name'],
                metric_cells(row['qty']), metric_cells(row['amount']), metric_cells(row['new']))

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

    # ------------------------------------------------------------------
    # HTML (vista en pantalla)
    # ------------------------------------------------------------------

    def _pct_class(self, pct, unbudgeted):
        if unbudgeted:
            return 'ns-unbud'
        if pct < -0.0001:
            return 'ns-neg'
        elif pct > 0.0001:
            return 'ns-pos'
        return 'ns-ok'

    def _render_table(self, title, first_col_label, rows, header_class):
        def fmt(v):
            return '{:,.2f}'.format(v)

        def pct_span(cell):
            cls = self._pct_class(cell['pct'], cell['unbudgeted'])
            return '<span class="ns-pct %s">%.0f%%</span>' % (cls, cell['pct'] * 100)

        month_headers = ''.join(
            '<th colspan="3">%s</th>' % label for _mm, label in self.MONTH_SELECTION
        )
        month_subheaders = ''.join(
            '<th>Objetivo</th><th>Real</th><th>Var %</th>' for _mm in self.MONTHS_ORDER
        )

        body_rows = ''
        for row in rows:
            tr_class = ' class="ns-total-row"' if row.get('is_total') else ''
            cells = ''
            for m in self.MONTHS_ORDER:
                cell = row['months'][m]
                cells += '<td>%s</td><td>%s</td><td>%s</td>' % (fmt(cell['obj']), fmt(cell['real']), pct_span(cell))
            total = row['total']
            body_rows += '<tr%s><td>%s</td>%s<td>%s</td><td>%s</td><td>%s</td></tr>' % (
                tr_class, row['name'], cells, fmt(total['obj']), fmt(total['real']), pct_span(total)
            )

        return '''
        <div class="ns-report-block">
          <div class="ns-report-title %s">%s</div>
          <table class="ns-report-table">
            <thead>
              <tr>
                <th rowspan="2">%s</th>
                %s
                <th colspan="3">Total</th>
              </tr>
              <tr>
                %s
                <th>Objetivo</th><th>Real</th><th>Var %%</th>
              </tr>
            </thead>
            <tbody>
              %s
            </tbody>
          </table>
        </div>
        ''' % (header_class, title, first_col_label, month_headers, month_subheaders, body_rows)

    def action_generate_report(self):
        self.ensure_one()
        team_rows = self._get_team_data()
        scheme_rows = self._get_scheme_data()
        region_category_rows = self._get_region_category_data()

        team_qty = self._metric_monthly_rows(team_rows, 'qty')
        team_amount = self._metric_monthly_rows(team_rows, 'amount')
        scheme_qty = self._metric_monthly_rows(scheme_rows, 'qty')
        scheme_amount = self._metric_monthly_rows(scheme_rows, 'amount')
        region_category_qty = self._metric_monthly_rows(region_category_rows, 'qty')
        region_category_amount = self._metric_monthly_rows(region_category_rows, 'amount')
        rows_mes, rows_acum = self._get_scheme_cutoff_data()
        month_label = dict(self._fields['month'].selection)[self.month]

        style = '''<style>
            .ns-report-block{margin-bottom:24px;overflow-x:auto;}
            .ns-report-title{padding:6px 10px;color:white;font-weight:bold;font-size:13px;}
            .ns-title-team{background:#C0006E;}
            .ns-title-scheme{background:#2E7D32;}
            .ns-title-region-category{background:#1565C0;}
            .ns-title-mes{background:#C0006E;}
            .ns-title-acum{background:#2E7D32;}
            .ns-report-chart{margin-bottom:8px;}
            .ns-chart-title{font-size:12px;font-weight:bold;margin-bottom:4px;}
            .ns-chart-legend{font-size:10px;color:#666;margin-top:2px;}
            .ns-leg-box{display:inline-block;width:9px;height:9px;}
            .ns-report-table{border-collapse:collapse;width:100%;font-size:12px;}
            .ns-report-table th, .ns-report-table td{border:1px solid #ddd;padding:4px 8px;text-align:right;white-space:nowrap;}
            .ns-report-table th{background:#f5f5f5;text-align:center;}
            .ns-report-table td:first-child, .ns-report-table th:first-child{text-align:left;}
            .ns-total-row td{font-weight:bold;border-top:2px solid #333;}
            .ns-pct{padding:1px 5px;border-radius:3px;}
            .ns-pos{background:#C6EFCE;color:#006100;}
            .ns-neg{background:#FFC7CE;color:#9C0006;}
            .ns-ok{background:#EDEDED;color:#595959;}
            .ns-unbud{background:#BDD7EE;color:#1F4E78;}
        </style>'''

        html = style
        html += self._bar_chart_svg(rows_mes, 'qty', '# Facturado — %s' % month_label)
        html += self._render_cutoff_table(month_label, rows_mes, 'ns-title-mes')
        html += self._bar_chart_svg(rows_acum, 'qty', '# Facturado — Acumulado a %s' % month_label)
        html += self._render_cutoff_table('Acumulado a %s' % month_label, rows_acum, 'ns-title-acum')
        html += self._render_table(_('Presupuesto por Región — Cantidad'), _('Región'), team_qty, 'ns-title-team')
        html += self._render_table(_('Presupuesto por Región — Monto'), _('Región'), team_amount, 'ns-title-team')
        html += self._render_table(_('Presupuesto por Esquema — Cantidad'), _('Esquema'), scheme_qty, 'ns-title-scheme')
        html += self._render_table(_('Presupuesto por Esquema — Monto'), _('Esquema'), scheme_amount, 'ns-title-scheme')
        html += self._render_table(_('Presupuesto por Categoría de Cliente y Región — Cantidad'), _('Categoría / Región'), region_category_qty, 'ns-title-region-category')
        html += self._render_table(_('Presupuesto por Categoría de Cliente y Región — Monto'), _('Categoría / Región'), region_category_amount, 'ns-title-region-category')

        self.report_html = html
        return True

    # ------------------------------------------------------------------
    # Excel
    # ------------------------------------------------------------------

    def action_export_excel(self):
        self.ensure_one()
        from odoo.tools.misc import xlsxwriter

        team_rows = self._get_team_data()
        scheme_rows = self._get_scheme_data()
        region_category_rows = self._get_region_category_data()

        rows_mes, rows_acum = self._get_scheme_cutoff_data()
        month_label = dict(self._fields['month'].selection)[self.month]

        sheets = [
            ('Región - Cantidad', _('Región'), self._metric_monthly_rows(team_rows, 'qty'), '#C0006E'),
            ('Región - Monto', _('Región'), self._metric_monthly_rows(team_rows, 'amount'), '#C0006E'),
            ('Esquema - Cantidad', _('Esquema'), self._metric_monthly_rows(scheme_rows, 'qty'), '#2E7D32'),
            ('Esquema - Monto', _('Esquema'), self._metric_monthly_rows(scheme_rows, 'amount'), '#2E7D32'),
            ('Categoría-Región - Cantidad', _('Categoría / Región'), self._metric_monthly_rows(region_category_rows, 'qty'), '#1565C0'),
            ('Categoría-Región - Monto', _('Categoría / Región'), self._metric_monthly_rows(region_category_rows, 'amount'), '#1565C0'),
        ]

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sub_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1, 'align': 'center'})
        label_fmt = workbook.add_format({'border': 1})
        label_total_fmt = workbook.add_format({'border': 1, 'bold': True})
        num_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        num_total_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'bold': True})
        pct_fmts = {
            'ns-neg': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#FFC7CE', 'font_color': '#9C0006'}),
            'ns-ok': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#EDEDED', 'font_color': '#595959'}),
            'ns-pos': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#C6EFCE', 'font_color': '#006100'}),
            'ns-unbud': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#BDD7EE', 'font_color': '#1F4E78'}),
        }

        def write_cutoff_sheet(sheet_name, rows, color):
            header_fmt = workbook.add_format({'bold': True, 'bg_color': color, 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            ws = workbook.add_worksheet(sheet_name)
            ws.merge_range(0, 0, 1, 0, 'Esquema', header_fmt)
            col = 1
            for group_title in ('# Facturado', '$ Facturado', '# Clientes Nuevos'):
                ws.merge_range(0, col, 0, col + 3, group_title, header_fmt)
                for i, sub in enumerate(('Objetivo', 'Real', 'Var #', 'Var %')):
                    ws.write(1, col + i, sub, sub_header_fmt)
                col += 4
            ws.set_column(0, 0, 26)
            ws.set_column(1, col - 1, 11)
            ws.freeze_panes(2, 1)
            row_idx = 2
            for r in rows:
                is_total = r.get('is_total')
                ws.write(row_idx, 0, r['name'], label_total_fmt if is_total else label_fmt)
                nfmt = num_total_fmt if is_total else num_fmt
                col = 1
                for key in ('qty', 'amount', 'new'):
                    o, real, delta, pct, unbudgeted = r[key]
                    ws.write(row_idx, col, o, nfmt)
                    ws.write(row_idx, col + 1, real, nfmt)
                    ws.write(row_idx, col + 2, delta, nfmt)
                    ws.write(row_idx, col + 3, pct, pct_fmts[self._pct_class(pct, unbudgeted)])
                    col += 4
                row_idx += 1

        write_cutoff_sheet('Esquema - %s' % month_label, rows_mes, '#C0006E')
        write_cutoff_sheet('Esquema - Acum a %s' % month_label, rows_acum, '#2E7D32')

        for sheet_name, first_col_label, rows, color in sheets:
            header_fmt = workbook.add_format({'bold': True, 'bg_color': color, 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            ws = workbook.add_worksheet(sheet_name)

            ws.merge_range(0, 0, 1, 0, first_col_label, header_fmt)
            col = 1
            for _mm, label in self.MONTH_SELECTION:
                ws.merge_range(0, col, 0, col + 2, label, header_fmt)
                ws.write(1, col, 'Objetivo', sub_header_fmt)
                ws.write(1, col + 1, 'Real', sub_header_fmt)
                ws.write(1, col + 2, 'Var %', sub_header_fmt)
                col += 3
            ws.merge_range(0, col, 0, col + 2, 'Total', header_fmt)
            ws.write(1, col, 'Objetivo', sub_header_fmt)
            ws.write(1, col + 1, 'Real', sub_header_fmt)
            ws.write(1, col + 2, 'Var %', sub_header_fmt)
            total_col = col

            ws.set_column(0, 0, 26)
            ws.set_column(1, total_col + 2, 10)
            ws.freeze_panes(2, 1)

            row_idx = 2
            for row in rows:
                is_total = row.get('is_total')
                lfmt = label_total_fmt if is_total else label_fmt
                nfmt = num_total_fmt if is_total else num_fmt
                ws.write(row_idx, 0, row['name'], lfmt)
                col = 1
                for m in self.MONTHS_ORDER:
                    cell = row['months'][m]
                    ws.write(row_idx, col, cell['obj'], nfmt)
                    ws.write(row_idx, col + 1, cell['real'], nfmt)
                    ws.write(row_idx, col + 2, cell['pct'], pct_fmts[self._pct_class(cell['pct'], cell['unbudgeted'])])
                    col += 3
                total = row['total']
                ws.write(row_idx, total_col, total['obj'], nfmt)
                ws.write(row_idx, total_col + 1, total['real'], nfmt)
                ws.write(row_idx, total_col + 2, total['pct'], pct_fmts[self._pct_class(total['pct'], total['unbudgeted'])])
                row_idx += 1

        workbook.close()
        xlsx_data = output.getvalue()

        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Dashboard_Presupuesto_%s_%s.xlsx' % (self.budget_id.name or self.budget_id.id, month_label),
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
