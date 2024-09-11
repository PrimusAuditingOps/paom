from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class SaleOrder(models.Model):

    _inherit='sale.order'
    
    
    pao_fans_request_ids = fields.One2many(
        comodel_name='pao.globalgap.fans.request',
        inverse_name='sale_order_id',
        string='Fans request',
    )

    pao_fans_request_count = fields.Integer(
        compute='_get_fans_request'
    )

    @api.depends('pao_fans_request_ids')
    def _get_fans_request(self):
        for order in self:
            order.pao_fans_request_count = len(order.pao_fans_request_ids)

    def action_view_fans_request(self):
        self.ensure_one()     
        action = {
            'res_model': 'pao.globalgap.fans.request',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _("Fans request - %s", self.name),
            'domain': [('sale_order_id', '=', self.id)],
        }
        return action

    def send_sale_order_fans_request(self):
        self.ensure_one()
        return {
            'name': _('Fans Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'pao.globalgap.send.fans.request',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_capturist_id': self.partner_id.id}
        }