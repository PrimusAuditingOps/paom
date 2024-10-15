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
        # domain=lambda self: self.get_domain(),
        required=True
    )
    
    @api.model
    def default_get(self, fields):
        res = super(SendRaWizard, self).default_get(fields)
        
        self.set_domain()

        return res
    
    # @api.onchange('purchase_order_id')
    def set_domain(self):
        _logger.warning("changing")
        po_id = self.env.context.get("default_purchase_order_id")
        if po_id:
            # Set the domain based on the value of field_a
            return {
                'domain': {
                    'pao_registration_numbers_ids': [('id', 'in', self.get_domain(po_id))]
                }
            }
        else:
            # Clear the domain if field_a is not set
            return {
                'domain': {
                    'pao_registration_numbers_ids': []
                }
            }
    
    @api.model
    def get_domain(self, po_id):
        listnumbers = []
        _logger.warning(po_id)
        po = self.env['purchase.order'].browse(int(po_id))
        if po:
            for line in po.order_line:
                if line.registrynumber_id and line.registrynumber_id.id not in listnumbers:
                    listnumbers.append(line.registrynumber_id.id)
        _logger.warning(listnumbers)
        return listnumbers
        # domain = [('id', 'in', listnumbers)]
        # _logger.warning(domain)
        # return domain
    
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
    