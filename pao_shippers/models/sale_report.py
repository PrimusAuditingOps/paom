from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    pao_shipper_id = fields.Many2one('pao.shippers', 'Shipper', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['pao_shipper_id'] = ", partner.pao_shipper_id as pao_shipper_id"
        groupby += ', partner.pao_shipper_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)