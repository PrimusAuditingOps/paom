from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import uuid

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    ra_sent = fields.Boolean(default=False)
    ra_document_ids = fields.One2many(
        comodel_name='ra.document',
        inverse_name='purchase_order_id',
        string="RA Documents",
        domain=[('status', '!=', 'cancel')]
    )
    ra_documents_count = fields.Integer(compute="_get_ra_documents_count")
    
    today = fields.Date(store=False)
    
    registration_number_id = fields.Many2one('servicereferralagreement.registrynumber', string="Registration Number", compute="_get_po_registration_number", store=True)
    organization_id = fields.Many2one('servicereferralagreement.organization', string="Organization", compute="_get_po_organization", store=True)

    def _generate_access_token(self):
        for rec in self:
            if not rec.access_token:
                rec.access_token = str(uuid.uuid4())
            return rec.access_token
    
    @api.depends('order_line')
    def _get_po_registration_number(self):
        for rec in self:
            rec.registration_number_id = None
            line_with_rn = rec.order_line.filtered('registrynumber_id')
            if line_with_rn:
                rec.registration_number_id = line_with_rn[0].registrynumber_id.id
                
    @api.depends('order_line')
    def _get_po_organization(self):
        for rec in self:
            rec.organization_id = None
            line_with_org = rec.order_line.filtered('organization_id')
            if line_with_org:
                rec.organization_id = line_with_org[0].organization_id.id

    def _get_ra_documents_count(self):
        for rec in self:
            rec.ra_documents_count = len(rec.ra_document_ids)
            
    def action_view_linked_ra(self):
        self.ensure_one()
        return {
            'res_model': 'ra.document',
            'type': 'ir.actions.act_window',
            'name': _("Referral Agreements - %s", self.name),
            'view_mode': 'tree,form' if len(self.ra_document_ids) > 1 else 'form',
            'res_id': self.ra_document_ids[0].id if len(self.ra_document_ids) == 1 else False,
            'domain': [('purchase_order_id', '=', self.id), ('status', '!=', 'cancel')],
        }
    
    def sign_ra_action(self, ra_document): 
            
        mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{ra_document.create_uid.id}">@{ra_document.create_uid.name}</a>'

        message = _('Hello %(mention_html)s, the auditor has signed and accepted the RA.'
                ) % {'mention_html': mention_html}
        
        message = self.message_post(
            body=message,
            partner_ids=[ra_document.create_uid.partner_id.id],
            body_is_html = True
        )
        
        self.message_notify(
            message_id=message.id,
        )
    
    def notify_ra_request_progress(self, message):
        odoo_bot = self.env.ref('base.partner_root')
        self.message_post(
            body=message,
            message_type='notification',
            # subtype_xmlid='mail.mt_comment',
            author_id=odoo_bot.id
        )
        
    def get_ra_document(self, attribute):
        if not self.ra_document_ids:
            return '0'
        else:
            if attribute == 'id':
                return str(self.ra_document_ids[0].id)
            elif attribute == 'token':
                return str(self.ra_document_ids[0].access_token)
    
    def send_referral_agreement_action(self, ra_document_id = None, resend_action=False, subject=None, registration_numbers_ids=None, request_travel_expenses=True, reminder_days = 0, template_id = None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        
        if not self.coordinator_id:
            raise ValidationError(_("You must select a coordinator to proceed with the process."))
        
        if not self.coordinator_id.employee_ids[0].es_sign_signature:
            raise ValidationError(_("The coordinator doesn't have a registered signature."))
        
        line_with_org = self.order_line.filtered('organization_id')
        if not line_with_org:
            raise ValidationError(_("You must select an organization in the order lines to procced with the process."))
        
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_ids': self.ids,
            'default_ra_document_id': ra_document_id,
            'default_purchase_order_id': self.id,
            'default_resend_action': resend_action,
            'default_reminder_days': reminder_days,
            'default_registration_numbers_to_sign_ids': registration_numbers_ids,
            'default_request_travel_expenses': request_travel_expenses,
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
        })
        
        if subject:
            ctx.update({
                'default_subject': subject,
            })

        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)

        return {
            'name': _('Send RA'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'send.ra.wizard',
            'view_id': self.env.ref('pao_sign_ra.send_ra_wizard_view_form').id,
            'target': 'new',
            'context': ctx,
        }
    