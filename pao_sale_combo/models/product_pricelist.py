# -*- coding: utf-8 -*-
from odoo import Command, api, fields, models

from .pao_sale_combo import is_combo_company


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    pao_combo_ids = fields.One2many(
        comodel_name='pao.pricelist.combo',
        inverse_name='pricelist_id',
        string='Combos',
        copy=True,
    )
    pao_combo_enabled = fields.Boolean(compute='_compute_pao_combo_enabled')

    @api.depends('company_id')
    @api.depends_context('company')
    def _compute_pao_combo_enabled(self):
        for pricelist in self:
            pricelist.pao_combo_enabled = is_combo_company(pricelist.company_id or self.env.company)

    def _pao_get_combo_price(self, combo, product):
        """Price of a product inside a combo for this pricelist, 0 when it is not configured."""
        self.ensure_one()
        # sudo: the price is also recomputed for users without access to the pricelist configuration.
        pricelist_combo = self.sudo().pao_combo_ids.filtered(lambda c: c.combo_id == combo)[:1]
        line = pricelist_combo.line_ids.filtered(lambda l: l.product_id == product)[:1]
        return line.price if line else 0.0


class PaoPricelistCombo(models.Model):
    _name = 'pao.pricelist.combo'
    _description = 'Pricelist Combo'
    _rec_name = 'combo_id'
    _order = 'sequence, id'
    _check_company_auto = True

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(related='pricelist_id.company_id', store=True)
    currency_id = fields.Many2one(related='pricelist_id.currency_id')
    sequence = fields.Integer(default=10)
    combo_id = fields.Many2one(
        comodel_name='pao.sale.combo',
        string='Combo',
        required=True,
        ondelete='cascade',
        check_company=True,
    )
    line_ids = fields.One2many(
        comodel_name='pao.pricelist.combo.line',
        inverse_name='pricelist_combo_id',
        string='Prices',
        copy=True,
    )
    total_price = fields.Monetary(string='Total', compute='_compute_total_price', currency_field='currency_id')

    _sql_constraints = [
        ('pricelist_combo_uniq', 'unique(pricelist_id, combo_id)', 'A combo can only be once in the same pricelist.'),
    ]

    @api.depends('line_ids.price')
    def _compute_total_price(self):
        for pricelist_combo in self:
            pricelist_combo.total_price = sum(pricelist_combo.line_ids.mapped('price'))

    @api.onchange('combo_id')
    def _onchange_combo_id(self):
        """Load the products of the combo, keeping the prices already typed for them."""
        prices = {line.product_id: line.price for line in self.line_ids}
        self.line_ids = [Command.clear()] + [
            Command.create({
                'sequence': combo_line.sequence,
                'product_id': combo_line.product_id.id,
                'price': prices.get(combo_line.product_id, 0.0),
            })
            for combo_line in self.combo_id.line_ids
        ]

    def action_pao_sync_products(self):
        """Align the prices with the current products of the combo (new products start at 0)."""
        for pricelist_combo in self:
            combo_products = pricelist_combo.combo_id.line_ids.product_id
            pricelist_combo.line_ids.filtered(lambda l: l.product_id not in combo_products).unlink()
            existing = pricelist_combo.line_ids.product_id
            pricelist_combo.line_ids = [
                Command.create({'sequence': combo_line.sequence, 'product_id': combo_line.product_id.id, 'price': 0.0})
                for combo_line in pricelist_combo.combo_id.line_ids
                if combo_line.product_id not in existing
            ]
        return True


class PaoPricelistComboLine(models.Model):
    _name = 'pao.pricelist.combo.line'
    _description = 'Pricelist Combo Price'
    _order = 'sequence, id'

    pricelist_combo_id = fields.Many2one(
        comodel_name='pao.pricelist.combo',
        required=True,
        ondelete='cascade',
        index=True,
    )
    currency_id = fields.Many2one(related='pricelist_combo_id.currency_id')
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    price = fields.Monetary(string='Unit Price', currency_field='currency_id')

    _sql_constraints = [
        ('pricelist_combo_product_uniq', 'unique(pricelist_combo_id, product_id)',
         'A product can only have one price in the same combo of a pricelist.'),
    ]
