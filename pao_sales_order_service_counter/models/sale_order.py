from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit='sale.order'

    pao_service_counter = fields.Integer(string="Total Service Lines", compute='_pao_compute_service_counter',store=True)
    
    @api.depends("order_line")
    def _pao_compute_service_counter(self):
        for rec in self:
            rec.pao_service_counter = len(rec.order_line.filtered(lambda ol: ol.product_id and not ol.product_id.is_travel_expenses and ol.product_id.can_be_commissionable))