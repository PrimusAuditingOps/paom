from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from logging import getLogger
from datetime import datetime
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang
from werkzeug.urls import url_join

_logger = getLogger(__name__)

class PaoGlobalgapSendFansRequest(models.TransientModel):
    _name = 'pao.globalgap.send.fans.request'
    _description = 'PAO GLOBALG.A.P. send fans request'


    capturist_id = fields.Many2one(
        'res.partner', 
        string="Capturist",
        required=True,
    )
    follower_ids = fields.Many2many('res.partner', string="Copy to")
    subject = fields.Char(
        string="Subject", 
        required=True, 
        default=_("Solicitud de registro de aplicación GLOBALG.A.P"),
    )
    message = fields.Html(
        string="Message",
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale order',
        ondelete='set null',
    )
    fans_request_id = fields.Many2one(
        comodel_name='pao.globalgap.fans.request',
        string='Fan request',
        ondelete='set null',
    )
    send_to_sign = fields.Boolean(
        string="Send to Sign",
        default=False,
    )
    
    def send_fans_request(self):
        self.ensure_one()

        if self.send_to_sign:
             #rec.write({"request_status": "annulled"})
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            form_url = url_join(base_url, '/pao/fan/signature/%s/%s' % (self.fans_request_id.id, self.fans_request_id.access_token))            

            #tpl = self.env.ref('pao_globalgap_fans.fans_request_signature_mail')
            customer_lang = get_lang(self.env, lang_code=self.capturist_id.lang).code
            #tpl = tpl.with_context(lang=customer_lang)
            body = self.env['ir.ui.view'].with_context(lang=customer_lang)._render_template('pao_globalgap_fans.fans_request_signature_mail',{
                    'record': self,
                    'link': form_url,
                    'subject': _("Signature Request"),
                    'body': self.message if self.message != '<p><br></p>' else False,
                }
            )
                        
            mail = self._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': self.fans_request_id.title},
                {'model_description': _('Signature Request'), 'company': self.fans_request_id.create_uid.company_id},
                {'email_from': self.fans_request_id.create_uid.email_formatted,
                    'author_id': self.fans_request_id.create_uid.partner_id.id,
                    'email_to': self.fans_request_id.organization_id.contact_email,
                    'subject': _('Signature Request')},
                force_send=True,
                lang=customer_lang,
            )
            self.fans_request_id.write({"request_status": "signature_request"})

        else:
            fr = None
            if not self.fans_request_id:
                fr = self.env['pao.globalgap.fans.request'].create({
                    'capturist_id': self.capturist_id.id,
                    'capturist_email': self.capturist_id.email,
                    'follower_ids': self.follower_ids,
                    'sale_order_id': self.sale_order_id.id,
                    'request_status': 'sent',            
                })
                
            else:
                old_attachment_id = None
                fr = self.fans_request_id
                if fr.attachment_id:
                    old_attachment_id = fr.attachment_id.id
                fr.write({"request_status": 'sent' if fr.request_status == "draft" else 'correction', "attachment_id": None})
                
                if old_attachment_id:
                    self.env['ir.attachment'].sudo().search([("id","=",old_attachment_id),("res_id","=",fr.id),("res_model","=","pao.globalgap.fans.request")]).unlink()


            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            form_url = url_join(base_url, '/pao/fillout/fans/%s/%s' % (fr.id, fr.access_token))
            fr.write({"request_url": form_url})

            #tpl = self.env.ref('pao_globalgap_fans.fans_request_template_mail')
            customer_lang = get_lang(self.env, lang_code=self.capturist_id.lang).code
            #tpl = tpl.with_context(lang=customer_lang)
            body = self.env['ir.ui.view'].with_context(lang=customer_lang)._render_template('pao_globalgap_fans.fans_request_template_mail',{
                    'record': fr,
                    'link': form_url,
                    'subject': self.subject,
                    'body': self.message if self.message != '<p><br></p>' else False,
                }
            )
            
            mail = self._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': fr.title},
                {'model_description': _('Formulario de aplicación'), 'company': self.create_uid.company_id},
                {'email_from': self.create_uid.email_formatted,
                    'author_id': self.create_uid.partner_id.id,
                    'email_to': self.capturist_id.email_formatted,
                    'subject': self.subject},
                force_send=True,
                lang=customer_lang,
            )
            if mail:
                #sa.write({'mail_id': mail.id})
                for follower in self.follower_ids:
                    #tpl = self.env.ref('pao_globalgap_fans.fans_request_template_mail')
                    follower_lang = get_lang(self.env, lang_code=follower.lang).code
                    #tpl = tpl.with_context(lang=follower.lang)
                    body = self.env['ir.ui.view'].with_context(lang=customer_lang)._render_template('pao_globalgap_fans.fans_request_template_mail',{
                        'record': fr,
                        'link': form_url,
                        'subject': self.subject,
                        'body': self.message if self.message != '<p><br></p>' else False,
                    })
                
                    mail = self._message_send_mail(
                        body, 'mail.mail_notification_light',
                        {'record_name': fr.title},
                        {'model_description': _('FR'), 'company': self.create_uid.company_id},
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

        #notif_layout = sign_request.env.ref(notif_template_xmlid)
        #body_html = notif_layout._render(dict(message=msg, **notif_values), engine='ir.qweb', minimal_qcontext=True)


        body_html =  self.env['ir.ui.view'].with_context(lang=lang)._render_template(notif_template_xmlid, 
            dict(message=msg, **notif_values)
        )

        body_html = sign_request.env['mail.render.mixin']._replace_local_links(body_html)

        mail = sign_request.env['mail.mail'].sudo().create(dict(body_html=body_html, state='outgoing', **mail_values))
        if force_send:
            mail.send()
        return mail
    