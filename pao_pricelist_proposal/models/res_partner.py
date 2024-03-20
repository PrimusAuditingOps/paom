from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    def notify_channel_action(self, message, channel_name, subject):
        # self.message_post(
        #     body=message, 
        #     subject="New message added"
        # )
        
        message = self.message_post(
            body=message,
        )

        channel = self.env['mail.channel'].search([('name', '=', channel_name)], limit=1)

        if channel:
            # Notify all members of the channel
            for member in channel.channel_partner_ids:
                member.message_post(body=message, subject=subject)