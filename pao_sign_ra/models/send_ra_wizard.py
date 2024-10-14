from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SendRaWizard(models.Model):

    _name = "send.ra.wizard"
    _inherit="mail.compose.message"
    _description = 'Send RA Wizard'
    
    extra_field = fields.Boolean(string="")
    
    attachment_ids = fields.Many2many(
        'ir.attachment', 'send_ra_wizard_ir_attachments_rel',
        'wizard_id', 'attachment_id', string='Attachments',
        compute='_compute_attachment_ids', readonly=False, store=True)
    
    partner_ids = fields.Many2many(
        'res.partner', 'send_ra_wizard_res_partner_rel',
        'wizard_id', 'partner_id', 'Additional Contacts',
        compute='_compute_partner_ids', readonly=False, store=True)
    