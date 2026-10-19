# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .pao_sale_combo import is_combo_company


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pao_combo_enabled = fields.Boolean(compute='_compute_pao_combo_enabled')

    @api.depends('company_id')
    def _compute_pao_combo_enabled(self):
        for order in self:
            order.pao_combo_enabled = is_combo_company(order.company_id)

    def action_pao_add_combo(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add a combo'),
            'res_model': 'pao.sale.combo.add',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }

    def _pao_add_combo(self, combo):
        """Append a section named after the combo with its products. The unit price comes from the
        combo prices of the order pricelist (see sale.order.line._compute_price_unit)."""
        self.ensure_one()
        if self.state == 'cancel' or self.locked:
            raise UserError(_("You cannot add a combo to a cancelled or locked order."))
        sequence = max(self.order_line.mapped('sequence'), default=0) + 1
        vals_list = [{
            'order_id': self.id,
            'display_type': 'line_section',
            'name': combo.name,
            'sequence': sequence,
        }]
        for index, combo_line in enumerate(combo.line_ids, start=1):
            vals_list.append({
                'order_id': self.id,
                'product_id': combo_line.product_id.id,
                'product_uom_qty': 1.0,
                'sequence': sequence + index,
                'pao_combo_id': combo.id,
            })
        return self.env['sale.order.line'].create(vals_list)
