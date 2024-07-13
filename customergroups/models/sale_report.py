from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    cgg_group_id = fields.Many2one('customergroups.group', 'Group', readonly=True)

    def _group_by_sale(self):
        """ Inherit function to add promotor_id """
        groupby_ = super(SaleReport, self)._group_by_sale()
        groupby_ += ', partner.cgg_group_id'
        return groupby_

    def _select_sale(self):
        """ Inherit function to add promotor_id """
        select_ = super(SaleReport, self)._select_sale()
        select_ += ', partner.cgg_group_id'
        return select_
