from odoo import models, fields

class AllowedTemplates(models.Model):
    _name = 'ra.mail.templates'
    _description = 'RA Allowed Email Templates'

    template_id = fields.Many2one('mail.template', string="Template", required=True, domain=[('model', '=', 'purchase.order')])

