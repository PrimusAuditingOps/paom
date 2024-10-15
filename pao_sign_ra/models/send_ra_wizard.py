from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from logging import getLogger

_logger = getLogger(__name__)

class SendRaWizard(models.Model):

    _name = "send.ra.wizard"
    _inherit="mail.compose.message"
    _description = 'Send RA Wizard'
    
    purchase_order_id = fields.Many2one('purchase.order', required=True)
    
    request_travel_expenses = fields.Boolean(default=True, string="Request Travel Expenses")
    
    pao_registration_numbers_ids = fields.Many2many(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registration Numbers',
        # domain=lambda self: self._get_registration_numbers_domain(),
        required=True
    )  
    
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
        
    @api.model
    def default_get(self, fields):
        res = super(SendRaWizard, self).default_get(fields)
        
        # Get the purchase_order_id from the context or any other source
        purchase_order_id = self.env.context.get('purchase_order_id')  # Assuming active_id is the purchase order
        _logger.warning(purchase_order_id)
        if purchase_order_id:
            purchase_order = self.env['purchase.order'].browse(purchase_order_id)
            listnumbers = []

            for line in purchase_order.order_line:
                if line.registrynumber_id and line.registrynumber_id.id not in listnumbers:
                    listnumbers.append(line.registrynumber_id.id)

            _logger.warning(listnumbers)  # Log the registration numbers
            
            # Set the domain for the Many2many field in the wizard context
            res['pao_registration_numbers_ids'] = [(6, 0, listnumbers)]
        
        return res
    
    # @api.model
    # def _get_registration_numbers_domain(self):
    #     for rec in self:
    #         listnumbers = []

    #         for line in rec.purchase_order_id.order_line:
    #             if line.registrynumber_id:
    #                 if line.registrynumber_id.id not in listnumbers:
    #                         listnumbers.append(line.registrynumber_id.id)
    #         _logger.warning(listnumbers)
    #         return [('id', 'in', listnumbers)]
    