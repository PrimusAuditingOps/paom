# -*- coding: utf-8 -*-
from odoo import _, api, fields, models

from .pao_sale_combo import is_combo_company


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    pao_combo_enabled = fields.Boolean(compute='_compute_pao_combo_enabled')

    @api.depends('company_id')
    @api.depends_context('company')
    def _compute_pao_combo_enabled(self):
        for template in self:
            template.pao_combo_enabled = is_combo_company(template.company_id or self.env.company)

    def action_pao_add_combo(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add a combo'),
            'res_model': 'pao.sale.combo.add',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_template_id': self.id},
        }

    def _pao_add_combo(self, combo):
        """Append a section named after the combo with its products, linked to the combo so the quotations
        created from this template price them with the combo prices of their pricelist."""
        self.ensure_one()
        sequence = max(self.sale_order_template_line_ids.mapped('sequence'), default=0) + 1
        vals_list = [{
            'sale_order_template_id': self.id,
            'display_type': 'line_section',
            'name': combo.name,
            'sequence': sequence,
        }]
        for index, combo_line in enumerate(combo.line_ids, start=1):
            vals_list.append({
                'sale_order_template_id': self.id,
                'product_id': combo_line.product_id.id,
                'product_uom_qty': 1.0,
                'sequence': sequence + index,
                'pao_combo_id': combo.id,
            })
        return self.env['sale.order.template.line'].create(vals_list)
