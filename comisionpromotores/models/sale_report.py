from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    promotor_id = fields.Many2one('comisionpromotores.promotor', 'Promoter', readonly=True)

    def _group_by_sale(self):
        """ Inherit function to add promotor_id """
        groupby_ = super(SaleReport, self)._group_by_sale()
        groupby_ += ', partner.promotor_id'
        return groupby_

    def _select_sale(self):
        """ Inherit function to add promotor_id """
        select_ = super(SaleReport, self)._select_sale()
        select_ += ', partner.promotor_id'
        return select_