from odoo import fields, models, api, _

from logging import getLogger

_logger = getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pao_customer_registration_ids = fields.One2many(
        comodel_name='pao.customer.registration',
        inverse_name='res_partner_id',
        string='Customer Registration Request',
    )
    pao_customer_registration_count = fields.Integer(
        compute='_get_customer_registration_request'
    )
    @api.depends('pao_customer_registration_ids')
    def _get_customer_registration_request(self):
        for order in self:
            order.pao_customer_registration_count = len(order.pao_customer_registration_ids)

    

    def action_view_customer_registration(self):
        self.ensure_one()     
        action = {
            'res_model': 'pao.customer.registration',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _("Customer Registration - %s", self.name),
            'domain': [('res_partner_id', '=', self.id)],
        }
        return action
    
    def send_customer_registration_request(self):
        self.ensure_one()
        return {
            'name': _('Customer Registration Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'pao.customer.registration.request',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_res_partner_id': self.id, 'default_contact_id': self.id}
        }