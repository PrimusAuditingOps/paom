# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pao_promotor_id = fields.Many2one(
        comodel_name='comisionpromotores.promotor',
        string='Commission Agent',
        help="Promoter who earns commission on this line. Auto-filled from "
             "the quotation's promoter (pao_promotor_id) for commissionable "
             "products; clear it manually to exclude this specific line from "
             "the commission calculation.",
    )
    pao_commission_payment = fields.Boolean(
        string='Commissionable Product',
        related='product_id.pao_commission_payment',
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'pao_promotor_id' in vals or not vals.get('order_id') or not vals.get('product_id'):
                continue
            order = self.env['sale.order'].browse(vals['order_id'])
            product = self.env['product.product'].browse(vals['product_id'])
            if order.pao_promotor_id and product.pao_commission_payment:
                vals['pao_promotor_id'] = order.pao_promotor_id.id
        return super().create(vals_list)

    @api.onchange('product_id')
    def _onchange_product_id_pao_promotor(self):
        for line in self:
            if line.product_id.pao_commission_payment and line.order_id.pao_promotor_id:
                line.pao_promotor_id = line.order_id.pao_promotor_id
            elif not line.product_id.pao_commission_payment:
                line.pao_promotor_id = False
