from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    ra_document_ids = fields.One2many(
        comodel_name='ra.document',
        inverse_name='purchase_order_id',
        string="RA Documents",
        domain=[('status', '!=', 'cancel')]
    )
    ra_documents_count = fields.Integer(compute="_get_ra_documents_count")
    
    def _get_ra_documents_count(self):
        for rec in self:
            rec.ra_documents_count = len(rec.ra_document_ids)
            
    def action_view_linked_ra(self):
        self.ensure_one()  
        action = {
            'res_model': 'ra.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _("Referral Agreements - %s", self.name),
            'domain': [('purchase_order_id', '=', self.id), ('status', '!=', 'cancel')],
        }
        return action
    
    def send_referral_agreement_action(self, resend_action=False, registration_numbers_ids=None, request_travel_expenses=True):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_ids': self.ids,
            'default_purchase_order_id': self.id,
            'default_resend_action': resend_action,
            'default_registration_numbers_to_sign_ids': registration_numbers_ids,
            'default_request_travel_expenses': request_travel_expenses,
            'default_template_id': False,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
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
    