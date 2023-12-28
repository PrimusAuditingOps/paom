from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from logging import getLogger
from datetime import datetime
from werkzeug.urls import url_join
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class PaoCustomerRegistrationRequest(models.TransientModel):
    _name = 'pao.customer.registration.request'
    _description = 'Customer Registration Request'


    contact_id = fields.Many2one(
        'res.partner', 
        string="Contact",
        required=True,
    )
    follower_ids = fields.Many2many('res.partner', string="Copy to")
    subject = fields.Char(
        string="Subject", 
        required=True, 
        default="",
    )

    message = fields.Html(
        string="Message",
    )
    res_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        ondelete='cascade',
    )
    
    def send_customer_registration_request(self):
        self.ensure_one()

        cr = self.env['pao.customer.registration'].create({
            'contact_id': self.contact_id.id,
            'res_partner_id': self.res_partner_id.id,
            'follower_ids': self.follower_ids,
            'name': self.res_partner_id.name,
            'country_id': self.res_partner_id.country_id.id,
            'state_id': self.res_partner_id.state_id.id,
            'city_id': self.res_partner_id.city_id.id,
            'street_name': self.res_partner_id.street,
            'street_number': self.res_partner_id.street2,
            'zip': self.res_partner_id.zip,
            'phone': self.res_partner_id.phone,
            'email': self.res_partner_id.email,
            'subject': self.subject,
            'message': self.message,
            'cfdi_use': self.res_partner_id.ctm_cfdi_use,
            'vat': self.res_partner_id.vat,
            
        })
        
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        form_url = url_join(base_url, '/pao/customer/registration/%s/%s' % (cr.id, cr.access_token))
        cr.write({"form_url": form_url})

        tpl = self.env.ref('pao_customer_registration.rc_template_mail_request')
        customer_lang = get_lang(self.env, lang_code=self.contact_id.lang).code
        tpl = tpl.with_context(lang=customer_lang)
        body = tpl._render({
                'record': cr,
                'link': form_url,
                'subject': self.subject,
                'body': self.message if self.message != '<p><br></p>' else False,
            }, engine='ir.qweb', minimal_qcontext=True)
        
        
        mail = self._message_send_mail(
            body, 'mail.mail_notification_light',
            {'record_name': cr.name},
            {'model_description': _('CR'), 'company': self.create_uid.company_id},
            {'email_from': self.create_uid.email_formatted,
                'author_id': self.create_uid.partner_id.id,
                'email_to': self.contact_id.email_formatted,
                'subject': self.subject},
            force_send=True,
            lang=customer_lang,
        )
        if mail:
            #sa.write({'mail_id': mail.id})
            for follower in self.follower_ids:
                tpl = self.env.ref('pao_customer_registration.rc_template_mail_request')
                follower_lang = get_lang(self.env, lang_code=follower.lang).code
                tpl = tpl.with_context(lang=follower.lang)
                body = tpl._render({
                    'record': cr,
                    'link': form_url,
                    'subject': self.subject,
                    'body': self.message if self.message != '<p><br></p>' else False,
                }, engine='ir.qweb', minimal_qcontext=True)
                
                mail = self._message_send_mail(
                    body, 'mail.mail_notification_light',
                    {'record_name': cr.name},
                    {'model_description': _('CR'), 'company': self.create_uid.company_id},
                    {'email_from': self.create_uid.email_formatted,
                        'author_id': self.create_uid.partner_id.id,
                        'email_to': follower.email_formatted,
                        'subject': self.subject},
                    force_send=True,
                    lang=follower_lang,
                )

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

