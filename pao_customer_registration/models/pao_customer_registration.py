from odoo import fields, models, api, _
import uuid
from logging import getLogger
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class PaoCustomerRegistration(models.Model):
    _name='pao.customer.registration'
    _description = 'Customer Registration'
    

    @api.model
    def _default_access_token(self):
        return uuid.uuid4().hex
    name = fields.Char(
        string="Name",
    )
    vat = fields.Char(
        string="VAT",
    )
    country_id = fields.Many2one(
        string="Country",
        comodel_name='res.country',
        ondelete='set null',
    )
    state_id = fields.Many2one(
        string="State",
        comodel_name='res.country.state',
        ondelete='set null',
    )
    city_id = fields.Many2one(
        string="City",
        comodel_name='res.city',
        ondelete='set null',
    )
    street_name = fields.Char(
        string="Street name",
    )
    street_number = fields.Char(
        string="Street number",
    )
    asesor = fields.Char(
        string="Asesor",
    )
    zip = fields.Char(
        string="ZIP",
    )
    phone = fields.Char(
        string="Phone",
    )
    email = fields.Char(
        string="Email",
    )
    cfdi_use = fields.Char(
        string="CFDI use",
    )
    form_url = fields.Char(
        string="Form URL",
    )
    follower_ids = fields.Many2many('res.partner', string="Copy to")
    subject = fields.Char(
        string="Subject", 
    )

    message = fields.Html(
        string="Message",
    )
    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment',
        ondelete='restrict',
        copy=False,
    )
    attachment_datas = fields.Binary(
        related='attachment_id.datas',
        string="Constancy",
    )
    attachment_name = fields.Char(
        related='attachment_id.name',
    )
    attachment_proof_of_address_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment',
        ondelete='restrict',
        copy=False,
    )
    attachment_proof_of_address_datas = fields.Binary(
        related='attachment_proof_of_address_id.datas',
        string="Proof of address",
    )
    attachment_proof_of_address_name = fields.Char(
        related='attachment_proof_of_address_id.name',
    )
    attachment_bank_account_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment',
        ondelete='restrict',
        copy=False,
    )
    attachment_bank_account_datas = fields.Binary(
        related='attachment_bank_account_id.datas',
        string="Bank account statement cover",
    )
    attachment_bank_account_name = fields.Char(
        related='attachment_bank_account_id.name',
    )
    attachment_sat_compliance_opinion_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment',
        ondelete='restrict',
        copy=False,
    )
    attachment_sat_compliance_opinion_datas = fields.Binary(
        related='attachment_sat_compliance_opinion_id.datas',
        string="Bank account statement cover",
    )
    attachment_sat_compliance_opinion_name = fields.Char(
        related='attachment_sat_compliance_opinion_id.name',
    )



    res_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        ondelete='cascade',
        required=True,
    )
    
    contact_id = fields.Many2one(
        'res.partner', 
        string="Contact",
        required=True,
    )
    request_status = fields.Selection(
        selection=[
            ('sent', "Sent"),
            ('complet', "Completed"),
            ('cancel', "Cancelled"),
            ('exception', "Mail Failed"),
            ('done', "Done"),
        ],
        string="Request Status",
        readonly=True, copy=False, index=True,
        default='sent'
    )
    access_token = fields.Char(
        'Security Token', 
        default=_default_access_token,
        copy=False,
    )

    child_ids = fields.One2many(
        comodel_name='pao.customer.registration.contact',
        inverse_name='customer_registration_id',
        string='Contacts',
    )

    def action_resend(self):
        self.ensure_one()
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        tpl = self.env.ref('pao_customer_registration.rc_template_mail_request')
        customer_lang = get_lang(self.env, lang_code=self.contact_id.lang).code
        tpl = tpl.with_context(lang=customer_lang)

        body = tpl._render({
                'record': self,
                'link': self.form_url,
                'subject': self.subject,
                'body': self.message if self.message != '<p><br></p>' else False,
            }, engine='ir.qweb', minimal_qcontext=True)

       
        mail = self._message_send_mail(
            body, 'mail.mail_notification_light',
            {'record_name': self.name},
            {'model_description': _('CR'), 'company': self.create_uid.company_id},
            {'email_from': self.create_uid.email_formatted,
                'author_id': self.create_uid.partner_id.id,
                'email_to': self.contact_id.email_formatted,
                'subject': self.subject},
            force_send=True,
            lang=customer_lang,
        )
        if mail:
            
            for follower in self.follower_ids:
                tpl = self.env.ref('pao_customer_registration.rc_template_mail_request')
                follower_lang = get_lang(self.env, lang_code=follower.lang).code
                tpl = tpl.with_context(lang=follower.lang)
                body = tpl._render({
                    'record': self,
                    'link': self.form_url,
                    'subject': self.subject,
                    'body': self.message if self.message != '<p><br></p>' else False,
                }, engine='ir.qweb', minimal_qcontext=True)
                
                mail = self._message_send_mail(
                    body, 'mail.mail_notification_light',
                    {'record_name': self.name},
                    {'model_description': _('CR'), 'company': self.create_uid.company_id},
                    {'email_from': self.create_uid.email_formatted,
                        'author_id': self.create_uid.partner_id.id,
                        'email_to': follower.email_formatted,
                        'subject': self.subject},
                    force_send=True,
                    lang=follower_lang,
                )
        """
        self.write(
            {
                "request_status": "sent"
            }
        )

    def action_cancel(self):
        self.ensure_one()
        self.write({"request_status": "cancel"})

    def action_update_contact(self):
        self.ensure_one()

        self.write(
            {
                "request_status": "done"
            }
        )
        partner = self.res_partner_id
        partner.write(
            {
                "name": self.name,
                "vat": self.vat,
                "country_id": self.country_id.id,
                "state_id": self.state_id.id,
                "city_id": self.city_id.id,
                "street": self.street_name,
                "zip": self.zip,
                "phone": self.phone,
                "email": self.email,
                "ctm_cfdi_use": self.cfdi_use,
            }
        )
        attachment_list = []
        if self.attachment_id:
            attachment_list.append(self.attachment_id.id)
        if self.attachment_proof_of_address_id:
            attachment_list.append(self.attachment_proof_of_address_id.id)
        if self.attachment_bank_account_id:
            attachment_list.append(self.attachment_bank_account_id.id)
        if self.attachment_sat_compliance_opinion_id:
            attachment_list.append(self.attachment_sat_compliance_opinion_id.id)

        contact = self.env["res.partner"]
        for rec in self.child_ids:
            contact.create(
                {
                    "type": "contact",
                    "name": rec.name,
                    "function": rec.occupation,
                    "email": rec.email,
                    "phone": rec.phone,
                    "parent_id": partner.id,
                }
            )
        partner.message_post(body=_("The fiscal certificate has been added."), attachment_ids= attachment_list)

    def _message_send_mail(self, body, notif_template_xmlid, message_values, notif_values, mail_values, force_send=False, **kwargs):
        
        default_lang = get_lang(self.env, lang_code=kwargs.get('lang')).code
        lang = kwargs.get('lang', default_lang)
        sign_request = self.with_context(lang=lang)

        msg = sign_request.env['mail.message'].sudo().new(dict(body=body, **message_values))
        notif_layout = sign_request.env.ref(notif_template_xmlid)
        body_html = notif_layout._render(dict(message=msg, **notif_values), engine='ir.qweb', minimal_qcontext=True)
        body_html = sign_request.env['mail.render.mixin']._replace_local_links(body_html)

        mail = sign_request.env['mail.mail'].sudo().create(dict(body_html=body_html, state='outgoing', **mail_values))
        if force_send:
            mail.send()
        return mail