from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from logging import getLogger
import uuid

_logger = getLogger(__name__)


class RADocument(models.Model):
    _name = 'ra.document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
    
    company_id = fields.Many2one(related="purchase_order_id.company_id")
    
    coordinator_id = fields.Many2one(related="purchase_order_id.coordinator_id", string="Coordinator")
    
    partner_id = fields.Many2one(related="purchase_order_id.partner_id", string="Signer")
    
    customer_id = fields.Many2one(related="purchase_order_id.sale_order_id.partner_id", string="Customer")
    
    organization_id = fields.Many2one('servicereferralagreement.organization', string="Organization", compute="_get_organization")

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
        
    reminder_days = fields.Integer(string = 'Reminder days', default = 0)
    
    ra_sent_date = fields.Date()
    
    ra_template_id = fields.Many2one('mail.template', readonly=True)
    
    @api.model
    def _get_access_token(self):
        return uuid.uuid4().hex
    
    def _get_organization(self):
        for rec in self:
            rec.organization_id = None
            if rec.purchase_order_id:
                line_with_org = rec.purchase_order_id.order_line.filtered('organization_id')
                if line_with_org:
                    rec.organization_id = line_with_org[0].organization_id.id
    
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
            return self.purchase_order_id.send_referral_agreement_action(
                ra_document_id = self.id,
                resend_action=True, 
                registration_numbers_ids=self.pao_registration_numbers_ids.ids, 
                request_travel_expenses = self.request_travel_expenses, 
                reminder_days = self.reminder_days,
                template_id = self.ra_template_id.id
            )
    
    def action_cancel(self):
        if self.status in ('sent', 'sign'):
            previous_status = self.status
            self.status = 'cancel'
            
            if self.purchase_order_id.ra_documents_count <= 0:
                self.purchase_order_id.ra_sent = False
                if previous_status == 'sign':
                    auditconfirmation = self.env['auditconfirmation.purchaseconfirmation'].sudo().search([('ac_id_purchase','=',self.purchase_order_id.id)])
                    auditconfirmation.write({'ac_audit_confirmation_status': '0'})
                    self.purchase_order_id.write({'sra_audit_signature': None, 'sra_audit_signature_name': None, 'sra_audit_signature_date': None})
                    message=_('The previously signed RA has been canceled.')
                    self.purchase_order_id.notify_ra_request_progress(message)
            
                
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': self.purchase_order_id.id, 
                'target': 'current', 
            }
            
    def action_test_reminder(self):
        self._send_ra_reminders()
            
    @api.model
    def _send_ra_reminders(self):
        today = fields.Date.today()

        ra_records_to_remind = self.search([
            ('reminder_days', '>', 0),
            ('status', 'in', ['sent']),
        ])

        for rec in ra_records_to_remind:
            # Calculate how many days have passed since creation
            if not rec.ra_sent_date:
                continue
            days_passed = (today - rec.ra_sent_date).days

            if 0 < days_passed <= rec.reminder_days:
                wizard = self.env['send.ra.wizard'].create({
                    'purchase_order_id': rec.purchase_order_id.id,
                    'resend_action': True,
                    'reminder_days': rec.reminder_days,
                    'ra_document_id': rec.id,
                    'request_travel_expenses': rec.request_travel_expenses,
                    'template_id': rec.ra_template_id.id,
                    'composition_mode': 'comment',
                })
                wizard.action_send_mail()
                
                odoo_bot = self.env.ref('base.partner_root')
                self.message_post(
                    body=_("A reminder email was sent to the customer."),
                    message_type='notification',
                    # subtype_xmlid='mail.mt_comment',
                    author_id=odoo_bot.id
                )
