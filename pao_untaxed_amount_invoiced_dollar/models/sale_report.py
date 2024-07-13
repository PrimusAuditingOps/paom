from odoo import fields, models, api



class SaleReport(models.Model):
    _inherit = 'sale.report'

    pao_untaxed_amount_invoiced_dollar = fields.Float(
        'Importe en dólares sin impuestos facturado', #'Untaxed Amount Invoiced Dollar', 
        readonly=True,
    )

    def _select_sale(self):
        select_ = super(SaleReport, self)._select_sale()
        select_ += """,
            CASE WHEN l.product_id IS NOT NULL
                THEN sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0)
                    WHEN 0 THEN 1.0 ELSE s.currency_rate END) * CASE
                        WHEN prcr.rate IS NOT NULL THEN prcr.rate ELSE 1 END
            ELSE 0
            END as pao_untaxed_amount_invoiced_dollar
        """
        return select_

    def _from_sale(self):
        from_sale_ = super(SaleReport, self)._from_sale()
        from_sale_ += """ 
            LEFT JOIN res_currency_rate prcr 
                ON (prcr.name::date = s.date_order::date and prcr.currency_id = 2)
        """
        return from_sale_

    def _group_by_sale(self):
        group_by_ = super(SaleReport, self)._group_by_sale()
        group_by_ += ', prcr.rate'
        return group_by_
