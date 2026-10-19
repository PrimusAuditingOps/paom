# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PaoSaleComboAdd(models.TransientModel):
    _name = 'pao.sale.combo.add'
    _description = 'Add a Combo to a Quotation'

    # The combo is added either to a quotation or to a quotation template.
    order_id = fields.Many2one(comodel_name='sale.order', ondelete='cascade')
    template_id = fields.Many2one(comodel_name='sale.order.template', ondelete='cascade')
    company_id = fields.Many2one(comodel_name='res.company', compute='_compute_company_id')
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

    @api.depends('order_id', 'template_id')
    def _compute_company_id(self):
        for wizard in self:
            wizard.company_id = wizard.order_id.company_id or wizard.template_id.company_id or self.env.company

    @api.depends('combo_id', 'pricelist_id')
    def _compute_combo_info(self):
        for wizard in self:
            wizard.combo_product_ids = wizard.combo_id.line_ids.product_id
            wizard.in_pricelist = wizard.combo_id in wizard.pricelist_id.pao_combo_ids.combo_id

    def action_add(self):
        self.ensure_one()
        if self.order_id:
            self.order_id._pao_add_combo(self.combo_id)
        elif self.template_id:
            self.template_id._pao_add_combo(self.combo_id)
        return {'type': 'ir.actions.act_window_close'}
