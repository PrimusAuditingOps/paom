# -*- coding: utf-8 -*-
from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

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
    price = fields.Monetary(string='Combo Price', currency_field='currency_id')
    distribution_mode = fields.Selection(
        selection=[
            ('percentage', 'Percentage'),
            ('amount', 'Amount'),
        ],
        string='Distribute By',
        default='percentage',
        required=True,
        help="Percentage: type the share of each product, its price is computed from the combo price. "
             "Amount: type the price of each product, its share is computed from the combo price.",
    )
    lines_percentage = fields.Float(string='Total %', compute='_compute_lines_totals', digits=(16, 2))
    lines_price = fields.Monetary(string='Total Products', compute='_compute_lines_totals', currency_field='currency_id')

    _sql_constraints = [
        ('pricelist_combo_uniq', 'unique(pricelist_id, combo_id)', 'A combo can only be once in the same pricelist.'),
    ]

    @api.depends('line_ids.percentage', 'line_ids.price')
    def _compute_lines_totals(self):
        for pricelist_combo in self:
            pricelist_combo.lines_percentage = sum(pricelist_combo.line_ids.mapped('percentage'))
            pricelist_combo.lines_price = sum(pricelist_combo.line_ids.mapped('price'))

    # ------------------------------------------------------------
    # Distribution of the combo price among its products
    # ------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._pao_apply_distribution()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._pao_apply_distribution()
        return res

    @api.onchange('price', 'distribution_mode', 'line_ids')
    def _onchange_pao_distribution(self):
        for pricelist_combo in self:
            for line, values in pricelist_combo._pao_distributed_values().items():
                line.update(values)

    def _pao_distributed_values(self):
        """Values derived from the distribution mode: the product prices (percentage mode, the last product
        absorbs the rounding so the prices add up to the combo price) or the product shares (amount mode).

        :return: {line: {field: value}} for the lines whose values change
        """
        self.ensure_one()
        currency = self.currency_id or self.env.company.currency_id
        lines = self.line_ids.sorted('sequence')
        result = {}
        if self.distribution_mode == 'percentage':
            prices = [currency.round(self.price * line.percentage / 100.0) for line in lines]
            total_percentage = sum(lines.mapped('percentage'))
            if lines and float_compare(total_percentage, 100.0, precision_digits=2) == 0:
                prices[-1] = currency.round(self.price - sum(prices[:-1]))
            for line, price in zip(lines, prices):
                if currency.compare_amounts(line.price, price) != 0:
                    result[line] = {'price': price}
        else:
            for line in lines:
                percentage = float_round(line.price * 100.0 / self.price, precision_digits=2) if self.price else 0.0
                if float_compare(line.percentage, percentage, precision_digits=2) != 0:
                    result[line] = {'percentage': percentage}
        return result

    def _pao_apply_distribution(self):
        for pricelist_combo in self:
            for line, values in pricelist_combo._pao_distributed_values().items():
                line.write(values)
        if not self.env.context.get('pao_skip_combo_check'):
            self._pao_check_distribution()

    def _pao_check_distribution(self):
        """The shares must add up to 100% (percentage mode) and the product prices to the combo price."""
        for pricelist_combo in self.filtered('line_ids'):
            currency = pricelist_combo.currency_id or self.env.company.currency_id
            total_percentage = sum(pricelist_combo.line_ids.mapped('percentage'))
            total_price = sum(pricelist_combo.line_ids.mapped('price'))
            if (
                pricelist_combo.distribution_mode == 'percentage'
                and float_compare(total_percentage, 100.0, precision_digits=2) != 0
            ):
                raise ValidationError(_(
                    "The percentages of the products of the combo '%(combo)s' add up to %(total)s%% "
                    "instead of 100%% (difference: %(difference)s%%).",
                    combo=pricelist_combo.combo_id.display_name,
                    total=round(total_percentage, 2),
                    difference=round(100.0 - total_percentage, 2),
                ))
            if currency.compare_amounts(total_price, pricelist_combo.price) != 0:
                raise ValidationError(_(
                    "The prices of the products of the combo '%(combo)s' add up to %(total)s instead of the combo "
                    "price %(price)s (difference: %(difference)s).",
                    combo=pricelist_combo.combo_id.display_name,
                    total=currency.round(total_price),
                    price=currency.round(pricelist_combo.price),
                    difference=currency.round(pricelist_combo.price - total_price),
                ))

    @api.onchange('combo_id')
    def _onchange_combo_id(self):
        """Load the products of the combo, keeping the shares and prices already typed for them."""
        previous = {line.product_id: (line.percentage, line.price) for line in self.line_ids}
        self.line_ids = [Command.clear()] + [
            Command.create({
                'sequence': combo_line.sequence,
                'product_id': combo_line.product_id.id,
                'percentage': previous.get(combo_line.product_id, (0.0, 0.0))[0],
                'price': previous.get(combo_line.product_id, (0.0, 0.0))[1],
            })
            for combo_line in self.combo_id.line_ids
        ]

    def action_pao_sync_products(self):
        """Align the prices with the current products of the combo (new products start at 0). The distribution
        is not checked here: it is checked when the user saves the adjusted shares or prices."""
        for pricelist_combo in self.with_context(pao_skip_combo_check=True):
            combo_products = pricelist_combo.combo_id.line_ids.product_id
            pricelist_combo.line_ids.filtered(lambda l: l.product_id not in combo_products).unlink()
            existing = pricelist_combo.line_ids.product_id
            pricelist_combo.line_ids = [
                Command.create({
                    'sequence': combo_line.sequence,
                    'product_id': combo_line.product_id.id,
                    'percentage': 0.0,
                    'price': 0.0,
                })
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
    percentage = fields.Float(string='%', digits=(16, 2), help="Share of the combo price for this product.")
    price = fields.Monetary(string='Unit Price', currency_field='currency_id')

    _sql_constraints = [
        ('pricelist_combo_product_uniq', 'unique(pricelist_combo_id, product_id)',
         'A product can only have one price in the same combo of a pricelist.'),
    ]
