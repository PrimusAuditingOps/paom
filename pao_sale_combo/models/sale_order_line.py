# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pao_combo_id = fields.Many2one(
        comodel_name='pao.sale.combo',
        string='Combo',
        readonly=True,
        copy=True,
        index='btree_not_null',
        help="Combo that added this line. Its unit price comes from the combo prices of the order pricelist.",
    )

    def action_pao_add_combo(self):
        """'Add a combo' button of the order lines (same pattern as the native 'Catalog' button)."""
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.action_pao_add_combo()

    def _pao_is_combo_line(self):
        self.ensure_one()
        return bool(self.pao_combo_id) and not self.display_type

    def _compute_price_unit(self):
        """Combo lines take the combo price of the order pricelist (0 when not configured) instead of the
        regular pricelist price; this also applies when the quantity changes or prices are updated."""
        combo_lines = self.filtered(lambda line: line._pao_is_combo_line())
        super(SaleOrderLine, self - combo_lines)._compute_price_unit()
        for line in combo_lines:
            # Same guards as the native method: keep manually edited prices of invoiced lines.
            if (
                line.qty_invoiced > 0
                or (line.product_id.expense_policy == 'cost' and line.is_expense)
                or line._is_discount_line()
            ):
                continue
            pricelist = line.order_id.pricelist_id
            price = pricelist._pao_get_combo_price(line.pao_combo_id, line.product_id) if pricelist else 0.0
            line = line.with_company(line.company_id)
            product_taxes = line.product_id.taxes_id._filter_taxes_by_company(line.company_id)
            line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
                price,
                line.currency_id or line.order_id.currency_id,
                product_taxes=product_taxes,
                fiscal_position=line.order_id.fiscal_position_id,
            )

    def _compute_discount(self):
        """The combo price is final: no pricelist discount on combo lines."""
        combo_lines = self.filtered(lambda line: line._pao_is_combo_line())
        super(SaleOrderLine, self - combo_lines)._compute_discount()
        combo_lines.discount = 0.0
