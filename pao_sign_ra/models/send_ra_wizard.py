from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SendRaWizard(models.Model):

    _name = "send.ra.wizard"
    _inherit="mail.compose.message"
    _description = 'Send RA Wizard'
    
    extra_field = fields.Boolean(string="")
    