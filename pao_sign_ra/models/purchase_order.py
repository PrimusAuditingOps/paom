from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    ra_sent = fields.Boolean(default=False)
    ra_document_ids = fields.One2many(
        comodel_name='ra.document',
        inverse_name='purchase_order_id',
        string="RA Documents",
    )
    
    def send_referral_agreement_action(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_ids': self.ids,
            'default_template_id': False,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
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