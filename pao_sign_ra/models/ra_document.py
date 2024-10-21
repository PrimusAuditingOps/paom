from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from logging import getLogger
import uuid

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
    
    access_token = fields.Char(
        'Access Token', 
        default=lambda self: self._get_access_token(),
        copy=False,
    )
    
    request_travel_expenses = fields.Boolean(string="Request Travel Expenses", readonly=True)
    
    travel_expenses_posted = fields.Boolean(default=False)
    
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
    
    @api.model
    def _get_access_token(self):
        return uuid.uuid4().hex
    
    def action_accept_url(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/ra_request/response/%s/%s' % (self.id, self.access_token),
            'target': 'new'
        }
        
    def action_reject_url(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/ra_request/decline/%s/%s' % (self.id, self.access_token),
            'target': 'new'
        }
    
    def _set_document_name(self):
        for rec in self:
            registration_numbers_names = rec.pao_registration_numbers_ids.mapped('name')
            rec.name = rec.purchase_order_id.name + ' - ' + (', '.join(registration_numbers_names))
    
    def action_resend(self):
        if self.status == 'sent':
            return self.purchase_order_id.send_referral_agreement_action(resend_action=True, registration_numbers_ids=self.pao_registration_numbers_ids.ids, request_travel_expenses = self.request_travel_expenses)
    
    def action_cancel(self):
        if self.status == 'sent':
            self.status = 'cancel'
            
            if self.purchase_order_id.ra_documents_count <= 0:
                self.purchase_order_id.ra_sent = False
                
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': self.purchase_order_id.id, 
                'target': 'current', 
            }