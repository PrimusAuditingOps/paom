from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    cgg_group_id = fields.Many2one('customergroups.group', 'Group', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['cgg_group_id'] = ", partner.cgg_group_id as cgg_group_id"
        groupby += ', partner.cgg_group_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)