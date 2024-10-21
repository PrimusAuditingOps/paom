from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from logging import getLogger

_logger = getLogger(__name__)

class SendRaWizard(models.Model):

    _name = "send.ra.wizard"
    _inherit="mail.compose.message"
    _description = 'Send RA Wizard'
    
    purchase_order_id = fields.Many2one('purchase.order', required=True)
    
    ra_document_id = fields.Many2one('ra.document', default=None)
    
    resend_action = fields.Boolean(default=False)
    
    attachment_ids = fields.Many2many(
        'ir.attachment', 'send_ra_wizard_ir_attachments_rel',
        'wizard_id', 'attachment_id', string='Attachments',
        compute='_compute_attachment_ids', readonly=False, store=True)
    
    partner_ids = fields.Many2many(
        'res.partner', 'send_ra_wizard_res_partner_rel',
        'wizard_id', 'partner_id', 'Additional Contacts',
        compute='_compute_partner_ids', readonly=False, store=True)
    
    request_travel_expenses = fields.Boolean(default=True, string="Request Travel Expenses")
    
    registration_numbers_to_sign_ids = fields.Many2many(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registration Numbers',
    )
    
    available_registration_numbers_ids = fields.Many2many(
        'servicereferralagreement.registrynumber',
        'available_registration_numbers_registration_number_rel',
        string='Registration Numbers',
        readonly=True
    )
    
    ra_templates_ids = fields.Many2many('mail.template', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(SendRaWizard, self).default_get(fields)
        
        ra_templates = self.env['ra.mail.templates'].search([])
        res['ra_templates_ids'] = [(6, 0, ra_templates.mapped('template_id.id'))]
        
        purchase_order_id = self.env.context.get('default_purchase_order_id')
        resend_action = self.env.context.get('resend_action')
        if purchase_order_id and not resend_action:
            purchase_order = self.env['purchase.order'].browse(int(purchase_order_id))
            arr_ids = []

            for line in purchase_order.order_line:
                if line.registrynumber_id and line.registrynumber_id.id not in arr_ids and self._is_registration_number_available(line.registrynumber_id.id, purchase_order_id):
                    arr_ids.append(line.registrynumber_id.id)

            res['available_registration_numbers_ids'] = [(6, 0, arr_ids)]
        
        return res

    def _is_registration_number_available(self, registration_number_id, po_id):
        ra_documents = self.env['ra.document'].search([('purchase_order_id', '=', po_id), ('status', '!=', 'cancel')])
        for document in ra_documents:
            for document_registration_number in document.pao_registration_numbers_ids:
                if document_registration_number.id == registration_number_id:
                    return False
        return True
    
    def action_send_mail(self):
        if self.purchase_order_id:
            self.purchase_order_id.get_confirmation_access_token()
            if self.resend_action:
                self.ra_document_id.request_travel_expenses = self.request_travel_expenses
            else:
                self.purchase_order_id.ra_sent = True
                self.env["ra.document"].create({
                    'pao_registration_numbers_ids': self.available_registration_numbers_ids,
                    'purchase_order_id': self.purchase_order_id.id,
                    'request_travel_expenses': self.request_travel_expenses
                })
        
        # Re-render template with the values of the RA documents related to the PO
        super(SendRaWizard, self)._compute_body()
            
        super(SendRaWizard, self).action_send_mail()
    