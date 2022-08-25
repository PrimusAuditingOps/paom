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
    default_status = fields.Boolean(
        string= "Default status",
        default= False,
    )
    @api.constrains('default_status')
    def _validate_default_status(self):
        for rec in self:
            if rec.default_status == True:
                domain = [("id","<>",rec.id),("default_status","=", True)] if rec.id else [("default_status","=", True)]
                recstatus = self.env["auditconfirmation.auditstate"].search(domain, limit=1)
                for status in recstatus:
                    raise ValidationError(_("A default audit status is already assigned."))
