# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    pao_sales_commission_ids = fields.One2many(
        comodel_name='pao.sales.commission', inverse_name='purchase_order_id',
        string='Related Commissions',
    )
    pao_sales_commission_count = fields.Integer(
        string='# Commissions', compute='_compute_pao_sales_commission_count',
    )

    def _compute_pao_sales_commission_count(self):
        for order in self:
            order.pao_sales_commission_count = len(order.pao_sales_commission_ids)

    def action_view_pao_sales_commissions(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'pao_sales_commission_management.action_pao_sales_commission'
        )
        action['domain'] = [('purchase_order_id', '=', self.id)]
        return action
