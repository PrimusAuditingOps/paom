from odoo import fields, models



class SaleReport(models.Model):
    _inherit='sale.report'

    pao_shipper_id = fields.Many2one('pao.shippers', 'Shipper', readonly=True)

    def _select_sale(self):
        select_ = super(SaleReport, self)._select_sale()
        select_ += ', partner.pao_shipper_id as pao_shipper_id'
        return select_

    def _group_by_sale(self):
        group_by_ = super(SaleReport, self)._group_by_sale()
        group_by_ += ', partner.pao_shipper_id'
        return group_by_
