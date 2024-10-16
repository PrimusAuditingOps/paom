from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from logging import getLogger

_logger = getLogger(__name__)

class SendRaWizard(models.Model):

    _name = "send.ra.wizard"
    _inherit="mail.compose.message"
    _description = 'Send RA Wizard'
    
    purchase_order_id = fields.Many2one('purchase.order', required=True, default=1)
    
    request_travel_expenses = fields.Boolean(default=True, string="Request Travel Expenses")
    
    pao_registration_numbers_ids = fields.Many2many(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registration Numbers',
        required=True
    )
    
    filtered_registration_numbers = fields.Many2many(
        'servicereferralagreement.registrynumber',
        'filtered_registration_numbers_registry_number_rel',
        string='Registration Numbers',
        readonly=True
    )
    
    template_id = fields.Many2one('mail.template', domain=[('model', '=', 'send.ra.wizard')])
    
    @api.model
    def default_get(self, fields):
        res = super(SendRaWizard, self).default_get(fields)
        
        purchase_order_id = self.env.context.get('default_purchase_order_id')
        if purchase_order_id:
            purchase_order = self.env['purchase.order'].browse(int(purchase_order_id))
            arr_ids = []

            for line in purchase_order.order_line:
                if line.registrynumber_id and line.registrynumber_id.id not in arr_ids:
                    arr_ids.append(line.registrynumber_id.id)

            res['filtered_registration_numbers'] = [(6, 0, arr_ids)]
        
        return res
    
    attachment_ids = fields.Many2many(
        'ir.attachment', 'send_ra_wizard_ir_attachments_rel',
        'wizard_id', 'attachment_id', string='Attachments',
        compute='_compute_attachment_ids', readonly=False, store=True)
    
    partner_ids = fields.Many2many(
        'res.partner', 'send_ra_wizard_res_partner_rel',
        'wizard_id', 'partner_id', 'Additional Contacts',
        compute='_compute_partner_ids', readonly=False, store=True)
    
    
    def action_send_mail(self):
        if self.purchase_order_id:
            self.purchase_order_id.ra_sent = True
            self.purchase_order_id.ac_request_travel_expenses = self.request_travel_expenses
            # CREATE RA_DOCUMENT AND LINK IT TO PO
            
        super(SendRaWizard, self).action_send_mail()
    