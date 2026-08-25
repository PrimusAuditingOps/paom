import math
from collections import defaultdict

from odoo import models, fields, api, _


class PAOSalesBudgetProfitabilityReportWizard(models.TransientModel):
    _name = 'pao.sales.budget.profitability.report.wizard'
    _description = 'PAO Sales Budget - Reporte de Rentabilidad (Costo Proveedores / Costo Operativo / Pago Fijo / Ganancia)'

    # Un color por rubro, elegido para que combinen entre sí (paleta análoga
    # cálido/frío con buen contraste contra texto blanco).
    COLOR_PROVIDER = '#264653'
    COLOR_OPERATIONAL = '#E9C46A'
    COLOR_SAVINGS = '#F4A261'
    COLOR_PROFIT = '#2A9D8F'

    budget_id = fields.Many2one('pao.sales.budget', string='Presupuesto', required=True)
    report_html = fields.Html(string='Reporte', readonly=True, sanitize=False)

    # ------------------------------------------------------------------
    # Agregación
    # ------------------------------------------------------------------

    def _segments_from_lines(self, lines):
        """Suma los 5 montos relevantes (ingreso total y los 4 rubros de
        costo/ganancia) sobre un conjunto de líneas, y regresa la lista de
        segmentos (label, monto, color) lista para dibujar, en el mismo orden
        que la leyenda del prototipo: Costo operativo, Costo Proveedores,
        Pago Fijo, Ganancia.
        """
        total = sum(lines.mapped('total_amount'))
        provider = sum(lines.mapped('provider_cost_amount'))
        operational = sum(lines.mapped('operational_cost_amount'))
        savings = sum(lines.mapped('savings_amount'))
        profit = sum(lines.mapped('net_profit_amount'))
        segments = [
            (_('Costo operativo'), operational, self.COLOR_OPERATIONAL),
            (_('Costo Proveedores'), provider, self.COLOR_PROVIDER),
            (_('Pago Fijo'), savings, self.COLOR_SAVINGS),
            (_('Ganancia'), profit, self.COLOR_PROFIT),
        ]
        return total, segments

    def _get_report_data(self):
        """Regresa una lista de bloques a graficar: uno general, uno por cada
        esquema presente en el presupuesto, y uno por cada cuenta analítica
        que tenga esquemas asignados y comparta al menos uno con los esquemas
        vendidos en este presupuesto. Cada bloque es
        (título, subtítulo_total, (total, segments)).
        """
        self.ensure_one()
        budget = self.budget_id
        lines = budget.line_ids

        blocks = [(
            _('Presupuestado'),
            _('Total ingresos'),
            self._segments_from_lines(lines),
        )]

        schemes = lines.mapped('pao_sales_budget_scheme_id')
        scheme_blocks = []
        for scheme in schemes.sorted('name'):
            scheme_lines = lines.filtered(lambda l: l.pao_sales_budget_scheme_id == scheme)
            scheme_blocks.append((
                scheme.name,
                _('Total esquema'),
                self._segments_from_lines(scheme_lines),
            ))

        AnalyticAccount = self.env['account.analytic.account'].sudo()
        analytic_accounts = AnalyticAccount.search([
            ('pao_sales_budget_scheme_ids', 'in', schemes.ids),
        ], order='name')
        analytic_blocks = []
        for account in analytic_accounts:
            account_lines = lines.filtered(
                lambda l: l.pao_sales_budget_scheme_id in account.pao_sales_budget_scheme_ids)
            if not account_lines:
                continue
            analytic_blocks.append((
                account.name,
                _('Total cuenta analítica'),
                self._segments_from_lines(account_lines),
            ))

        return blocks, scheme_blocks, analytic_blocks

    # ------------------------------------------------------------------
    # SVG (gráfica de pastel a mano, mismo enfoque que ya usa el módulo en
    # pao_sales_budget_scheme_report_wizard para las barras)
    # ------------------------------------------------------------------

    def _pie_svg(self, title, total_label, total, segments, size=200):
        currency_symbol = self.budget_id.currency_id.symbol or ''

        def fmt_money(v):
            return '{}{:,.2f}'.format(currency_symbol, v)

        cx = cy = size / 2.0
        r = size / 2.0 - 8
        start_angle = -90.0  # arranca arriba (12 en punto), como el prototipo

        paths = ''
        legend_items = ''
        for label, amount, color in segments:
            frac = (amount / total) if total else 0.0
            sweep = frac * 360.0
            end_angle = start_angle + sweep
            x1 = cx + r * math.cos(math.radians(start_angle))
            y1 = cy + r * math.sin(math.radians(start_angle))
            x2 = cx + r * math.cos(math.radians(end_angle))
            y2 = cy + r * math.sin(math.radians(end_angle))
            large_arc = 1 if sweep > 180 else 0
            path_d = 'M%.2f,%.2f L%.2f,%.2f A%.2f,%.2f 0 %d 1 %.2f,%.2f Z' % (
                cx, cy, x1, y1, r, r, large_arc, x2, y2)
            pct = frac * 100
            # <title> da un tooltip nativo del navegador al pasar el mouse,
            # sin necesitar JavaScript.
            paths += (
                '<path d="%s" fill="%s" stroke="white" stroke-width="1.5">'
                '<title>%s: %s (%.0f%%)</title></path>'
            ) % (path_d, color, label, fmt_money(amount), pct)

            if frac > 0.03:
                mid_angle = (start_angle + end_angle) / 2.0
                lx = cx + (r * 0.62) * math.cos(math.radians(mid_angle))
                ly = cy + (r * 0.62) * math.sin(math.radians(mid_angle))
                paths += (
                    '<text x="%.2f" y="%.2f" font-size="13" font-weight="bold" fill="white" '
                    'text-anchor="middle" dominant-baseline="middle">%.0f%%</text>'
                ) % (lx, ly, pct)

            legend_items += (
                '<div class="ns-pie-legend-item">'
                '<span class="ns-leg-box" style="background:%s;"></span>'
                '<span class="ns-leg-label">%s</span>'
                '<span class="ns-leg-amount">%s (%.0f%%)</span>'
                '</div>'
            ) % (color, label, fmt_money(amount), pct)
            start_angle = end_angle

        return '''
        <div class="ns-pie-block">
          <div class="ns-pie-title">%s</div>
          <div class="ns-pie-subtitle">%s %s</div>
          <svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">%s</svg>
          <div class="ns-pie-legend">%s</div>
        </div>
        ''' % (title, total_label, fmt_money(total), size, size, size, size, paths, legend_items)

    def _render_row(self, section_title, pies_html):
        return '''
        <div class="ns-pie-section">
          <div class="ns-pie-section-title">%s</div>
          <div class="ns-pie-row">%s</div>
        </div>
        ''' % (section_title, ''.join(pies_html))

    def action_generate_report(self):
        self.ensure_one()
        general_blocks, scheme_blocks, analytic_blocks = self._get_report_data()

        style = '''<style>
            .ns-pie-section{margin-bottom:28px;}
            .ns-pie-section-title{font-size:16px;font-weight:bold;text-align:center;margin-bottom:12px;color:#264653;}
            .ns-pie-row{display:flex;flex-wrap:wrap;justify-content:center;gap:24px;}
            .ns-pie-block{text-align:center;max-width:240px;}
            .ns-pie-title{font-weight:bold;font-size:13px;}
            .ns-pie-subtitle{font-size:11px;color:#666;margin-bottom:6px;}
            .ns-pie-legend{text-align:left;margin-top:8px;font-size:11px;}
            .ns-pie-legend-item{display:flex;align-items:center;gap:5px;margin-bottom:2px;}
            .ns-leg-box{display:inline-block;width:10px;height:10px;flex:0 0 auto;}
            .ns-leg-label{flex:1 1 auto;}
            .ns-leg-amount{font-weight:bold;white-space:nowrap;}
        </style>'''

        html = style
        html += self._render_row('', [self._pie_svg(t, sub, total, segs) for t, sub, (total, segs) in general_blocks])
        if scheme_blocks:
            html += self._render_row(
                _('Presupuestado por Esquema'),
                [self._pie_svg(t, sub, total, segs) for t, sub, (total, segs) in scheme_blocks])
        if analytic_blocks:
            html += self._render_row(
                _('Presupuesto por Cuenta Analítica'),
                [self._pie_svg(t, sub, total, segs) for t, sub, (total, segs) in analytic_blocks])

        self.report_html = html
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
