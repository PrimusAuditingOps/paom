# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PaoSaleComboAdd(models.TransientModel):
    _name = 'pao.sale.combo.add'
    _description = 'Add a Combo to a Quotation'

    order_id = fields.Many2one(comodel_name='sale.order', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='order_id.company_id')
    pricelist_id = fields.Many2one(related='order_id.pricelist_id')
    combo_id = fields.Many2one(
        comodel_name='pao.sale.combo',
        string='Combo',
        required=True,
        domain="[('company_id', '=', company_id)]",
    )
    combo_product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Products',
        compute='_compute_combo_info',
    )
    in_pricelist = fields.Boolean(compute='_compute_combo_info')

    @api.depends('combo_id', 'pricelist_id')
    def _compute_combo_info(self):
        for wizard in self:
            wizard.combo_product_ids = wizard.combo_id.line_ids.product_id
            wizard.in_pricelist = wizard.combo_id in wizard.pricelist_id.pao_combo_ids.combo_id

    def action_add(self):
        self.ensure_one()
        self.order_id._pao_add_combo(self.combo_id)
        return {'type': 'ir.actions.act_window_close'}
