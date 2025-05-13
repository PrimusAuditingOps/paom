from odoo import fields, models, api, _
from logging import getLogger
import uuid
import base64
from werkzeug.urls import url_join
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class PaoGlobalgapFansRequest(models.Model):
    _name = "pao.globalgap.fans.request"
    _description = "GLOBALG.A.P. fans request"
    _rec_name = 'title'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _default_access_token(self):
        return uuid.uuid4().hex

    def _get_name_request(self):
        for rec in self:
            rec.title = "FR" + str(rec.id)

    title = fields.Char(
        string='name', 
        compute='_get_name_request'
    )
    capturist_id = fields.Many2one(
        'res.partner', 
        string="Capturist customer",
    )
    capturist_email = fields.Char(
        string="Capturist customer Email",
    )
    follower_ids = fields.Many2many('res.partner', string="Copy to")
    
    signer_id = fields.Many2one(
        'res.partner', 
        string="Signer",
    )
    signer_email = fields.Char(
        string="Signer Email",
    )
    request_url = fields.Char(
        string="URL para firmar",
    )
    signature_date = fields.Date(
        string="Signature date",
    )
    signature_name = fields.Char(
        'Signature name',
        copy=False,
    )
    signature = fields.Binary(
        string="Signature", 
        copy=False,
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        ondelete='set null',
        tracking=True,
    )
    attachment_id = fields.Many2one(
        string="Document",
        comodel_name='ir.attachment',
        ondelete='restrict',
        copy=False,
        tracking=True,
    )
    attachment_datas = fields.Binary(
        related='attachment_id.datas',
        string="Fan",
    )
    attachment_name = fields.Char(
        related='attachment_id.name',
    )
    
    reminder_days = fields.Integer(string = 'Reminder days', default = 0)
    
    request_sent_date = fields.Date()
    

    request_status = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('sent', "Sent"),
            ('review', "In review"),
            ('correction', "Correction request"),
            ('signature_request', "Signature request"),
            ('signed', "Signed"),
            ('annulled', "Annulled"),
            ('rejected', "Rejected"),
        ],
        string="Request Status",
        tracking=True,
        readonly=True, copy=False, index=True,
        default='draft'
    )
    qa_status = fields.Selection(
        selection=[
            ('pending', "Pending"),
            ('approved', "Approved"),
        ],
        string="QA Status",
        tracking=True,
        readonly=True, copy=False, index=True,
        default='pending'
    )
    access_token = fields.Char(
        'Security Token', 
        default=_default_access_token,
        copy=False,
    )
    signature_name = fields.Char(
        'Signature name',
        copy=False,
    )
    signature = fields.Binary(
        string="Signature", 
        copy=False,
    )
    signature_date = fields.Date(
        string="Signer's signature date", 
        copy=False,
    )
    organization_id = fields.Many2one(
        comodel_name='pao.globalgap.organization',
        string='GLOBALG.A.P Organization',
        ondelete='restrict',
    )

    def action_approve(self):
        for rec in self:
            rec.write({"qa_status": "approved"})
    
    def action_cancel(self):
        for rec in self:
            rec.write({"request_status": "annulled"})


    
    def resend_fans_request(self):
        self.ensure_one()
        return {
            'name': _('Fans Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'pao.globalgap.send.fans.request',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_fans_request_id': self.id,
                'default_capturist_id': self.capturist_id.id,
                'default_subject': _("Solicitud de registro de aplicación GLOBALG.A.P") if self.request_status == "draft" else _("Solicitud de correción para el registro de aplicacion GLOBALG.A.P")
            }
        }
    def action_send_to_sign(self):
        self.ensure_one()
        return {
            'name': _('Send FAN to sign'),
            'type': 'ir.actions.act_window',
            'res_model': 'pao.globalgap.send.fans.request',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_send_to_sign': True,
                'default_fans_request_id': self.id,
                'default_capturist_id': self.capturist_id.id,
                'default_subject': _("Solicitud de firma para el registro de aplicación GLOBALG.A.P") if self.request_status == "draft" else _("Solicitud de firma para el registro de aplicacion GLOBALG.A.P")
            }
        }
        """
        for rec in self:
            #rec.write({"request_status": "annulled"})
            base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
            form_url = url_join(base_url, '/pao/fan/signature/%s/%s' % (rec.id, rec.access_token))            

            tpl = rec.env.ref('pao_globalgap_fans.fans_request_signature_mail')
            customer_lang = get_lang(rec.env, lang_code=rec.capturist_id.lang).code
            tpl = tpl.with_context(lang=customer_lang)
            body = tpl._render({
                    'record': rec,
                    'link': form_url,
                    'subject': _("Signature Request"),
                    'body': '<p><br></p>',
                }, engine='ir.qweb', minimal_qcontext=True)
            
            
            mail = self._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': rec.title},
                {'model_description': _('Signature Request'), 'company': rec.create_uid.company_id},
                {'email_from': rec.create_uid.email_formatted,
                    'author_id': rec.create_uid.partner_id.id,
                    'email_to': rec.organization_id.contact_email,
                    'subject': _('Signature Request')},
                force_send=True,
                lang=customer_lang,
            )
            rec.write({"request_status": "signature_request"})
        """    
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
    
    
    def _reminder_send_mail(self, body, notif_template_xmlid, message_values, notif_values, mail_values, force_send=False, **kwargs):
        
        default_lang = get_lang(self.env, lang_code=kwargs.get('lang')).code
        lang = kwargs.get('lang', default_lang)
        sign_request = self.with_context(lang=lang)

        msg = sign_request.env['mail.message'].sudo().new(dict(body=body, **message_values))
        body_html =  self.env['ir.ui.view'].with_context(lang=lang)._render_template(notif_template_xmlid, 
            dict(message=msg, **notif_values)
        )

        body_html = sign_request.env['mail.render.mixin']._replace_local_links(body_html)

        mail = sign_request.env['mail.mail'].sudo().create(dict(body_html=body_html, state='outgoing', **mail_values))
        if force_send:
            mail.send()
        return mail
    

    def set_signature_message(self):
        
        mention_html = f'<a href="/web#model=res.partner&amp;id={self.create_uid.partner_id.id}" class="o_mail_redirect" data-oe-id="{self.create_uid.partner_id.id}" data-oe-model="res.partner" target="_blank">@{self.create_uid.name}</a>'
        
        request_link = ('<a href="#" data-oe-model="pao.globalgap.fans.request" data-oe-id="%(request_id)d">%(name)s</a>'
                                ) % {'name': self.title, 'request_id': self.id}
        
        message = _('Hello %(mention_html)s, the request %(request_link)s has been signed.'
                            ) % {'mention_html': mention_html, 'request_link': request_link}
        message = self.message_post(
            body=message,
            partner_ids=[self.create_uid.partner_id.id],
            body_is_html = True
        )
        
        self.message_notify(
            message_id=message.id,
        )
    def set_fill_out_message(self):
        
        mention_html = f'<a href="/web#model=res.partner&amp;id={self.create_uid.partner_id.id}" class="o_mail_redirect" data-oe-id="{self.create_uid.partner_id.id}" data-oe-model="res.partner" target="_blank">@{self.create_uid.name}</a>'
        
        request_link = ('<a href="#" data-oe-model="pao.globalgap.fans.request" data-oe-id="%(request_id)d">%(name)s</a>'
                                ) % {'name': self.title, 'request_id': self.id}
        
        message = _('Hello %(mention_html)s, the request %(request_link)s has been corrected.') % {'mention_html': mention_html, 'request_link': request_link} if self.request_status == "correction" else _('Hello %(mention_html)s, the request %(request_link)s has been filled out.') % {'request_link': request_link, 'mention_html': mention_html}
        

        message = self.message_post(
            body=message,
            partner_ids=[self.create_uid.partner_id.id],
            body_is_html = True
        )
        
        self.message_notify(
            message_id=message.id,
        )
        
    @api.model
    def _send_fan_reminders(self):
        today = fields.Date.today()

        fans = self.search([
            ('reminder_days', '>', 0),
            ('request_status', 'in', ['signature_request', 'correction']),
        ])

        for fan in fans:
            # Calculate how many days have passed since creation
            if not fan.request_sent_date:
                continue
            days_passed = (today - fan.request_sent_date).days

            if 0 < days_passed <= fan.reminder_days:
                subject = ''
                base_url = fan.env['ir.config_parameter'].sudo().get_param('web.base.url')
                customer_lang = get_lang(fan.env, lang_code=fan.capturist_id.lang).code
                
                if fan.request_status == 'signature_request':
                    form_url = url_join(base_url, '/pao/fan/signature/%s/%s' % (fan.id, fan.access_token))            
                    subject = _("Solicitud de firma para el registro de aplicación GLOBALG.A.P") if fan.request_status == "draft" else _("Solicitud de firma para el registro de aplicacion GLOBALG.A.P")
                    template = 'pao_globalgap_fans.fans_reminder_request_signature_mail'
                    
                elif fan.request_status == 'correction':
                    form_url = url_join(base_url, '/pao/fillout/fans/%s/%s' % (fan.id, fan.access_token))
                    subject = _("Solicitud de registro de aplicación GLOBALG.A.P") if fan.request_status == "draft" else _("Solicitud de correción para el registro de aplicacion GLOBALG.A.P")
                    fan.write({"request_url": form_url})
                    template = 'pao_globalgap_fans.fans_reminder_request_template_mail'

                else:
                    continue

                body = fan.env['ir.ui.view'].with_context(lang=customer_lang)._render_template(template,{
                        'record': fan,
                        'link': form_url,
                        'subject': subject,
                        'body': False,
                    }
                )
                mail = fan._reminder_send_mail(
                    body, 'mail.mail_notification_light',
                    {'record_name': fan.title},
                    {'model_description': _('FAN Reminder'), 'company': fan.create_uid.company_id},
                    {'email_from': fan.create_uid.email_formatted,
                        'author_id': fan.create_uid.partner_id.id,
                        'email_to': fan.capturist_id.email_formatted,
                        'subject': subject},
                    force_send=True,
                    lang=customer_lang,
                )
                