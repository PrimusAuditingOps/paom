from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    pao_promotor_id = fields.Many2one('comisionpromotores.promotor', 'Quotation Consultant', readonly=True)

    def _group_by_sale(self):
        """ Inherit function to add pao_promotor_id """
        groupby_ = super(SaleReport, self)._group_by_sale()
        groupby_ += ', s.pao_promotor_id'
        return groupby_

    def _select_sale(self):
        """ Inherit function to add pao_promotor_id """
        select_ = super(SaleReport, self)._select_sale()
        select_ += ', s.pao_promotor_id'
        return select_