from odoo import fields, models, api


class SaleReport(models.Model):
    _inherit = "sale.report"

    pao_untaxed_amount_invoiced_dollar = fields.Float(
        'Importe en dólares sin impuestos facturado', #'Untaxed Amount Invoiced Dollar', 
        readonly=True,
    )


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['pao_untaxed_amount_invoiced_dollar'] = ", CASE WHEN l.product_id IS NOT NULL THEN sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) * CASE WHEN prcr.rate IS NOT NULL THEN prcr.rate ELSE 1 END ELSE 0 END as pao_untaxed_amount_invoiced_dollar"
        from_clause += " left join res_currency_rate prcr on (prcr.name::date = s.date_order::date and prcr.currency_id = 2)"
        groupby += ', prcr.rate'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)


