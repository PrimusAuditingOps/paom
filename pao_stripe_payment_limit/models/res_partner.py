
from odoo import fields, models, api, _


class ResPartnerInherit(models.Model):

    _inherit = 'res.partner'
    
    @api.onchange('email')
    def _onchange_email_stripe(self):
        email_list = self.email.split(',')
        if len(email_list) > 1:
            return {'warning': {
                'title': _("Information related to the contact's email"),
                'message': _("Please remember that when entering more than one email address in a Contact, the address positioned first will be the one to which payments for the client's invoices will be sent."),
            }}
