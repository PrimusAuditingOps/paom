from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    promotor_id = fields.Many2one('comisionpromotores.promotor', 'Promoter', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['promotor_id'] = ", partner.promotor_id as promotor_id"
        groupby += ', partner.promotor_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)