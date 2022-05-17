from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class AuditorState(models.Model):
    
    _name = 'auditconfirmation.auditstate'
    _description = 'Audit Status'

    name = fields.Char(
        required=True,
        string= "Status",
    )
    show_in_portal = fields.Boolean(
        string= "Show in portal",
        default= False,
    )
    color = fields.Integer(
         string="Color",
         required=True,
         default = 0,
    )