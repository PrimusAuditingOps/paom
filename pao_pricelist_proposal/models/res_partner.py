from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    def notify_channel_action(self, message, channel_name, subject):
        channel = self.env['mail.channel'].search([('name', '=', channel_name)], limit=1)
        
        message = self.message_post(
            body=message,
            partner_ids=channel.channel_partner_ids,
        )