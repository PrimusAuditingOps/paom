from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from logging import getLogger

_logger = getLogger(__name__)


class RADocument(models.Model):
    _name = 'ra.document'
    _description = 'RA Document'
    
    name = fields.Char('Name', compute="_set_document_name")
    status = fields.Selection(
        string="Status", 
        default="sent",
        selection=[
            ('sent', 'Sent'), 
            ('sign', 'Signed'),
            ('reject', 'Rejected'), 
            ('cancel', 'Cancelled')
        ]
    )
    
    request_travel_expenses = fields.Boolean(string="Request Travel Expenses", readonly=True)
    
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")
    
    pao_registration_numbers_ids = fields.Many2many(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registration Numbers',
        required=True
    )
    
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        ondelete='cascade',
        required=True,
    )
    
    def _set_document_name(self):
        for rec in self:
            registration_numbers_names = rec.pao_registration_numbers_ids.mapped('name')
            rec.name = rec.purchase_order_id.name + ' - ' + (', '.join(registration_numbers_names))
    
    def action_resend(self):
        if self.status == 'sent':
            _logger.warning("SE INTENTA")
            return self.purchase_order_id.send_referral_agreement_action(resend_action=True, registration_numbers_ids=self.pao_registration_numbers_ids, request_travel_expenses = self.request_travel_expenses)
        _logger.warning("sin exito")
    
    def action_cancel(self):
        if self.status == 'sent':
            self.status = 'cancel'