from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    def notify_channel_action(self, message, channel_name, subject):

        channel = self.env['mail.channel'].search([('name', 'ilike', "general")]) 
        if channel:
            channel.message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment')
            # notification = ('<a href="#" data-oe-model="pao.customer.registration" class="o_redirect" data-oe-id="%s">#%s</a>') % (cr_sudo.id, cr_sudo.res_partner_id.name,)
            
        message = self.message_post(
            body=message,
            partner_ids=channel.channel_partner_ids.ids,
        )
