import base64
import io

from odoo import models, fields, api, _


class PAOSalesBudgetDashboardWizard(models.TransientModel):
    _name = 'pao.sales.budget.dashboard.wizard'
    _description = 'PAO Sales Budget - Dashboard (Equipo de Ventas / Esquema, Objetivo vs Real)'

    budget_id = fields.Many2one('pao.sales.budget', string='Presupuesto', required=True)
    report_html = fields.Html(string='Reporte', readonly=True, sanitize=False)

    # ------------------------------------------------------------------
    # Agregación: Objetivo (pao.sales.budget.line) vs Real (pao.sales.budget.actual.line),
    # total del periodo completo del presupuesto (sin corte por mes).
    # ------------------------------------------------------------------

    def _budget_vs_actual_totals(self, groupby_field):
        """Regresa una lista de dicts, uno por valor de groupby_field (equipo o
        esquema), con los totales de cantidad y monto tanto de lo presupuestado
        como de lo realmente facturado. Usa union de llaves (equipos/esquemas)
        presentes en cualquiera de los dos lados, para no perder registros que
        solo tengan real sin presupuesto o viceversa.
        """
        self.ensure_one()
        Line = self.env['pao.sales.budget.line'].sudo()
        Actual = self.env['pao.sales.budget.actual.line'].sudo()

        def grouped(Model):
            groups = Model.read_group(
                [('budget_id', '=', self.budget_id.id)],
                fields=['total_quantity:sum', 'total_amount:sum'],
                groupby=[groupby_field],
            )
            result = {}
            for g in groups:
                val = g[groupby_field]
                key = val[0] if val else False
                name = val[1] if val else _('Sin asignar')
                result[key] = {
                    'name': name,
                    'qty': g['total_quantity'] or 0.0,
                    'amount': g['total_amount'] or 0.0,
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
                'qty_budget': (b or {}).get('qty', 0.0),
                'qty_actual': (a or {}).get('qty', 0.0),
                'amount_budget': (b or {}).get('amount', 0.0),
                'amount_actual': (a or {}).get('amount', 0.0),
            })
        rows.sort(key=lambda r: r['name'])
        return rows

    @api.model
    def _variance(self, obj, real):
        """Regresa (delta, fracción_var, sin_objetivo)."""
        if obj == 0:
            return (real - obj), (9.999 if real > 0 else 0.0), (real > 0)
        return (real - obj), ((real - obj) / obj), False

    def _metric_rows(self, base_rows, metric):
        """base_rows viene de _budget_vs_actual_totals. metric es 'qty' o 'amount'.
        Regresa filas listas para render con Objetivo/Real/Var #/Var %, más una
        fila de Total / General al final."""
        rows = []
        for r in base_rows:
            o = r['%s_budget' % metric]
            real = r['%s_actual' % metric]
            delta, pct, unbudgeted = self._variance(o, real)
            rows.append({'name': r['name'], 'obj': o, 'real': real, 'delta': delta, 'pct': pct, 'unbudgeted': unbudgeted})

        total_o = sum(r['obj'] for r in rows)
        total_r = sum(r['real'] for r in rows)
        delta, pct, unbudgeted = self._variance(total_o, total_r)
        rows.append({'name': _('Total / General'), 'obj': total_o, 'real': total_r,
                      'delta': delta, 'pct': pct, 'unbudgeted': unbudgeted, 'is_total': True})
        return rows

    def _get_team_data(self):
        return self._budget_vs_actual_totals('region_id')

    def _get_scheme_data(self):
        return self._budget_vs_actual_totals('pao_sales_budget_scheme_id')

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

        body_rows = ''
        for row in rows:
            tr_class = ' class="ns-total-row"' if row.get('is_total') else ''
            pct_cls = self._pct_class(row['pct'], row['unbudgeted'])
            body_rows += (
                '<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
                '<td><span class="ns-pct %s">%.0f%%</span></td></tr>'
            ) % (tr_class, row['name'], fmt(row['obj']), fmt(row['real']), fmt(row['delta']), pct_cls, row['pct'] * 100)

        return '''
        <div class="ns-report-block">
          <div class="ns-report-title %s">%s</div>
          <table class="ns-report-table">
            <thead>
              <tr>
                <th>%s</th>
                <th>Objetivo</th>
                <th>Real</th>
                <th>Var #</th>
                <th>Var %%</th>
              </tr>
            </thead>
            <tbody>
              %s
            </tbody>
          </table>
        </div>
        ''' % (header_class, title, first_col_label, body_rows)

    def action_generate_report(self):
        self.ensure_one()
        team_rows = self._get_team_data()
        scheme_rows = self._get_scheme_data()

        team_qty = self._metric_rows(team_rows, 'qty')
        team_amount = self._metric_rows(team_rows, 'amount')
        scheme_qty = self._metric_rows(scheme_rows, 'qty')
        scheme_amount = self._metric_rows(scheme_rows, 'amount')

        style = '''<style>
            .ns-report-block{margin-bottom:24px;overflow-x:auto;}
            .ns-report-title{padding:6px 10px;color:white;font-weight:bold;font-size:13px;}
            .ns-title-team{background:#C0006E;}
            .ns-title-scheme{background:#2E7D32;}
            .ns-report-table{border-collapse:collapse;width:100%;font-size:12px;max-width:640px;}
            .ns-report-table th, .ns-report-table td{border:1px solid #ddd;padding:4px 8px;text-align:right;white-space:nowrap;}
            .ns-report-table th{background:#f5f5f5;text-align:center;}
            .ns-report-table td:first-child, .ns-report-table th:first-child{text-align:left;}
            .ns-total-row td{font-weight:bold;border-top:2px solid #333;}
            .ns-pct{padding:1px 5px;border-radius:3px;}
            .ns-pos{background:#FFEB9C;color:#9C6500;}
            .ns-neg{background:#FFC7CE;color:#9C0006;}
            .ns-ok{background:#C6EFCE;color:#006100;}
            .ns-unbud{background:#BDD7EE;color:#1F4E78;}
        </style>'''

        html = style
        html += self._render_table(_('Presupuesto por Equipo de Ventas — Cantidad'), _('Equipo de Ventas'), team_qty, 'ns-title-team')
        html += self._render_table(_('Presupuesto por Equipo de Ventas — Monto'), _('Equipo de Ventas'), team_amount, 'ns-title-team')
        html += self._render_table(_('Presupuesto por Esquema — Cantidad'), _('Esquema'), scheme_qty, 'ns-title-scheme')
        html += self._render_table(_('Presupuesto por Esquema — Monto'), _('Esquema'), scheme_amount, 'ns-title-scheme')

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

        sheets = [
            ('Equipo - Cantidad', _('Equipo de Ventas'), self._metric_rows(team_rows, 'qty'), '#C0006E'),
            ('Equipo - Monto', _('Equipo de Ventas'), self._metric_rows(team_rows, 'amount'), '#C0006E'),
            ('Esquema - Cantidad', _('Esquema'), self._metric_rows(scheme_rows, 'qty'), '#2E7D32'),
            ('Esquema - Monto', _('Esquema'), self._metric_rows(scheme_rows, 'amount'), '#2E7D32'),
        ]

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        label_fmt = workbook.add_format({'border': 1})
        label_total_fmt = workbook.add_format({'border': 1, 'bold': True})
        num_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        num_total_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'bold': True})
        pct_fmts = {
            'ns-neg': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#FFC7CE', 'font_color': '#9C0006'}),
            'ns-ok': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#C6EFCE', 'font_color': '#006100'}),
            'ns-pos': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#FFEB9C', 'font_color': '#9C6500'}),
            'ns-unbud': workbook.add_format({'border': 1, 'num_format': '0.0%', 'bg_color': '#BDD7EE', 'font_color': '#1F4E78'}),
        }

        for sheet_name, first_col_label, rows, color in sheets:
            header_fmt = workbook.add_format({'bold': True, 'bg_color': color, 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            ws = workbook.add_worksheet(sheet_name)
            ws.write(0, 0, first_col_label, header_fmt)
            ws.write(0, 1, 'Objetivo', header_fmt)
            ws.write(0, 2, 'Real', header_fmt)
            ws.write(0, 3, 'Var #', header_fmt)
            ws.write(0, 4, 'Var %', header_fmt)
            ws.set_column(0, 0, 26)
            ws.set_column(1, 4, 13)
            ws.freeze_panes(1, 1)

            row_idx = 1
            for row in rows:
                is_total = row.get('is_total')
                lfmt = label_total_fmt if is_total else label_fmt
                nfmt = num_total_fmt if is_total else num_fmt
                pfmt = pct_fmts[self._pct_class(row['pct'], row['unbudgeted'])]
                ws.write(row_idx, 0, row['name'], lfmt)
                ws.write(row_idx, 1, row['obj'], nfmt)
                ws.write(row_idx, 2, row['real'], nfmt)
                ws.write(row_idx, 3, row['delta'], nfmt)
                ws.write(row_idx, 4, row['pct'], pfmt)
                row_idx += 1

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
