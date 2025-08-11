from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class SaleOrder(models.Model):

    _inherit='sale.order'
    
    
    pao_confirmation_letter_ids = fields.One2many(
        comodel_name='pao.confirmation.letter',
        inverse_name='sale_order_id',
        string='Letters of Confirmation',
    )

    pao_confirmation_letter_count = fields.Integer(
        compute='_get_confirmation_letter'
    )

    @api.depends('pao_confirmation_letter_ids')
    def _get_confirmation_letter(self):
        for order in self:
            order.pao_confirmation_letter_count = len(order.pao_confirmation_letter_ids)

    def action_so_pao_confirmation_letter_view(self):
        self.ensure_one()     
        action = {
            'res_model': 'pao.confirmation.letter',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('pao_confirmation_letter.pao_confirmation_letter_view_tree').id, 'tree'), (self.env.ref('pao_confirmation_letter.pao_confirmation_letter_view_form').id, 'form')],
            'name': _("Letters of Confirmation - %s", self.name),
            'domain': [('sale_order_id', '=', self.id)],
        }
        return action