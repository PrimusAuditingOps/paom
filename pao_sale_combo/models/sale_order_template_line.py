# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderTemplateLine(models.Model):
    _inherit = 'sale.order.template.line'

    pao_combo_id = fields.Many2one(
        comodel_name='pao.sale.combo',
        string='Combo',
        readonly=True,
        copy=True,
        index='btree_not_null',
        help="Combo that added this line. It is passed to the quotation lines created from this template.",
    )

    def action_pao_add_combo(self):
        """'Add a combo' button of the template lines (same pattern as the order lines button)."""
        template = self.env['sale.order.template'].browse(self.env.context.get('template_id'))
        return template.action_pao_add_combo()

    def _prepare_order_line_values(self):
        values = super()._prepare_order_line_values()
        if self.pao_combo_id and not self.display_type:
            values['pao_combo_id'] = self.pao_combo_id.id
        return values
