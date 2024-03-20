from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    def notify_channel_action(self, message, channels):

        self.message_post(
            body=message,
            # partner_ids=channel.channel_partner_ids.ids,
        )
        
        odoo_bot = self.env.ref('base.partner_root')
        
        for channel_name in channels:
            channel = self.env['mail.channel'].search([('name', 'ilike', channel_name)]) 
            if channel:
                channel.sudo().message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment', author_id=odoo_bot.id)
                # notification = ('<a href="#" data-oe-model="pao.customer.registration" class="o_redirect" data-oe-id="%s">#%s</a>') % (cr_sudo.id, cr_sudo.res_partner_id.name,)
            
