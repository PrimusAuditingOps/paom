from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    pao_is_a_master_sales_order = fields.Boolean(string='Is a Master Order', readonly=True)
    pao_is_a_child_sales_order = fields.Boolean(string='Is a Sub-Order', readonly=True)

    def _group_by_sale(self):
        """ Inherit function to add promotor_id """
        groupby_ = super(SaleReport, self)._group_by_sale()
        groupby_ += ', s.pao_is_a_master_sales_order, s.pao_is_a_child_sales_order'
        return groupby_

    def _select_sale(self):
        """ Inherit function to add promotor_id """
        select_ = super(SaleReport, self)._select_sale()
        select_ += ', s.pao_is_a_master_sales_order, s.pao_is_a_child_sales_order'
        return select_