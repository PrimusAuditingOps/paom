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
        domain=lambda self: self.get_domain(),
        required=True
    )
    
    @api.model
    def get_domain(self):
        domain = [('id', 'in', [1,2,3])]
        _logger.warning(domain)
        
        ids = str(self.res_ids).strip('[]')
        ids = ids.split(',')
        ids = [int(id.strip()) for id in ids]
        
        purchase_orders = self.env['purchase.order'].browse(ids)
        
        _logger.warning(purchase_orders)
        listnumbers = []
        for purchase_order in purchase_orders:
            for line in purchase_order.order_line:
                if line.registrynumber_id and line.registrynumber_id.id not in listnumbers:
                    listnumbers.append(line.registrynumber_id.id)

            _logger.warning(listnumbers)  # Log the registration numbers
        
        domain = [('id', 'in', listnumbers)]
        _logger.warning(domain)
        return domain
    
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