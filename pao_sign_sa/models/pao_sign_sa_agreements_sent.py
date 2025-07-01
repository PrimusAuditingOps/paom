from odoo import tools
from odoo import fields, models, api, _
from logging import getLogger
import uuid
import pytz
from datetime import datetime, timedelta
import dateutil.parser
from werkzeug.urls import url_join
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang
import base64
_logger = getLogger(__name__)

class PaoSignSaAgreementsSent(models.Model):
    _name = "pao.sign.sa.agreements.sent"
    _description = "Agreements Sent"
    _rec_name = 'title'


    @api.model
    def _default_access_token(self):
        return uuid.uuid4().hex

    def _generate__date_spanish(self):
        months = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
        day = None
        month = None
        year = None
        dateservice = None
        for rec in self:
            dateservice = dateutil.parser.parse(str(rec.create_date)).date()
            day = dateservice.day
            month = months[dateservice.month - 1]
            year = dateservice.year
            rec.date_complete_spanish = "{0} de {1} del {2}".format(day, month, year)
    def _generate__date_english(self):
        months = ("january", "febrary", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december")
        day = None
        month = None
        year = None
        dateservice = None
        for rec in self:
            dateservice = dateutil.parser.parse(str(rec.create_date)).date()
            day = dateservice.day
            month = months[dateservice.month - 1]
            year = dateservice.year
            rec.date_complete_english = "{0} {1}, {2}".format(month, day, year)

    title = fields.Char(
        string='name', 
        compute='_get_name_sa'
    )

    signer_id = fields.Many2one(
        'res.partner', 
        string="Signer",
        required=True,
    )
    signer_email = fields.Char(
        string="Signer Email",
    )
    date_complete_spanish = fields.Text(
        compute= _generate__date_spanish,
    )
    
    sign_url = fields.Char(
        string="URL para firmar",
    )
    date_complete_english = fields.Text(
        compute= _generate__date_english,
    )
    follower_ids = fields.Many2many('res.partner', string="Copy to")
    position = fields.Char(
        string="Title", 
        required=True
    )
    signer_name = fields.Char(
        string="Signer name", 
    )
    document_date = fields.Date(
        string="Document date",
    )
    signature_date = fields.Date(
        string="Signature date",
    )
    registration_numbers_ids = fields.Many2many(
        'servicereferralagreement.registrynumber', 
        'agreements_sent_registration_numbers_rel',
        'agreements_sent_id', 
        'registration_numbers_id', 
        'Registration Numbers',
        required=True,
    )
    subject = fields.Char(
        string="Subject", 
        required=True
    )
    message = fields.Html(
        string="Message",
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        ondelete='cascade',
        required=True,
    )
    
    customer_id = fields.Many2one(related="sale_order_id.partner_id", string="Customer")
    
    organization_id = fields.Char(string="Organization", compute="_compute_organizations")

    reminder_days = fields.Integer(
        string = 'Reminder days',
        default = 0,
    )
    document_status = fields.Selection(
        selection=[
            ('sent', "Sent"),
            ('partially_sign', "Partially signed"),
            ('sign', "Completely signed"),
            ('cancel', "Cancelled"),
            ('exception', "Mail Failed"),
        ],
        string="Document Status",
        readonly=True, copy=False, index=True,
        default='sent'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment', 
        'pao_sign_sa_agreements_sent_ir_attachments_rel',
        'agreements_sent_id', 
        'attachment_id', 
        'Attachments'
    )
    mail_id = fields.Many2one(
        comodel_name='mail.mail',
        string='Mail',
        ondelete='restrict',
        copy=False,
    )
    mail_state = fields.Selection(
        related="mail_id.state",
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
    
    coordinator_signature = fields.Binary(
        string="Coordinator Signature", 
        copy=False,
    )

    coordinator_name = fields.Char(string="Coordinator Name", copy=False)
    coordinator_signature_date = fields.Date(string="Coordinator's signature date", copy=False)

    signature = fields.Binary(
        string="Signature", 
        copy=False,
    )
    signature_date = fields.Date(
        string="Signer's signature date", 
        copy=False,
    )
    registration_number_to_sign_ids = fields.One2many(
        comodel_name='pao.registration.number.to.sign',
        inverse_name='sign_sa_agreements_id',
        string='Registration number IDs',
    )
    
    company_id = fields.Many2one(related="sale_order_id.company_id")

    country_format = fields.Selection(
        default=lambda self: self.env.company.country_code, 
        selection=[
            ('US', 'United States'),
            ('MX', 'México'),
            ('CR', 'Costa Rica'),
            ('CL', 'Chile'),
        ],
        string="Country Template",
    )

    @api.depends('registration_numbers_ids')
    def _get_name_sa(self):
        for rec in self:
            title_sa = ""
            for rn in rec.registration_numbers_ids:
                title_sa += rn.name  if title_sa == "" else ", " + rn.name
            rec.title = title_sa
            
    @api.depends('registration_numbers_ids', 'sale_order_id.order_line.registrynumber_id', 'sale_order_id.order_line.organization_id')
    def _compute_organizations(self):
        for rec in self:
            rec.organization_id = ''
            if rec.sale_order_id and rec.registration_numbers_ids:
                # Get IDs of registration numbers in this record
                target_rn_ids = rec.registration_numbers_ids.ids

                # Filter sale order lines that have matching registration numbers
                matching_lines = rec.sale_order_id.order_line.filtered(
                    lambda line: any(rn.id in target_rn_ids for rn in line.registrynumber_id)
                )

                # Get unique organization names from those lines
                org_names = {
                    line.organization_id.name
                    for line in matching_lines
                    if line.organization_id
                }

                # Join them as a comma-separated string
                rec.organization_id = ", ".join(sorted(org_names))
    
    def action_coordinator_sign(self):
        self.ensure_one()

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': '/coordinator_sign/sa/%s/%s' % (self.id, self.access_token),
            'target': 'new',  # Opens the URL in a new tab
        }
    
    def action_resend(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        signer_lang = get_lang(self.env, lang_code=self.signer_id.lang).code
        
        body =  self.env['ir.ui.view'].with_context(lang=signer_lang)._render_template('pao_sign_sa.sa_template_mail_request', 
            {
                'record': self,
                'link': url_join(base_url, '/sign/sa/%s/%s' % (self.id, self.access_token)),
                'subject': self.subject,
                'body': self.message if self.message != '<p><br></p>' else False,
            }
        )



        self._message_send_mail(
            body, 'mail.mail_notification_light',
            {'record_name': self.title},
            {'model_description': _('Service Agreement'), 'company': self.create_uid.company_id},
            {'email_from': self.create_uid.email_formatted,
                'author_id': self.create_uid.partner_id.id,
                'email_to': self.signer_id.email_formatted,
                'subject': self.subject},
            force_send=True,
            lang=signer_lang,
        )


    def action_cancel(self):
        self.ensure_one()
        self.write({"document_status": "cancel"})

    
    @api.model
    def _send_sa_signature_reminders(self):
        for sign_request in self.env['pao.sign.sa.agreements.sent'].search([('document_status', '=', 'sent'),('reminder_days', '>', 0)]):
             
            if not sign_request.create_date:
                continue            
             
            requested_tz = pytz.timezone(sign_request.create_uid.tz)
            today = requested_tz.fromutc(datetime.utcnow())
            reminder = sign_request.create_date + timedelta(days=sign_request.reminder_days)
            reminder = dateutil.parser.parse(str(reminder)).date()
            if today.date() > reminder:
                continue
            else:   
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                signer_lang = get_lang(self.env, lang_code=sign_request.signer_id.lang).code
                
               
                body =  self.env['ir.ui.view'].with_context(lang=signer_lang)._render_template('pao_sign_sa.sa_template_mail_request', 
                    {
                        'record': sign_request,
                        'link': url_join(base_url, '/sign/sa/%s/%s' % (sign_request.id, sign_request.access_token)),
                        'subject': sign_request.subject,
                        'body': sign_request.message if sign_request.message != '<p><br></p>' else False,
                    }
                )



                self._message_send_mail(
                    body, 'mail.mail_notification_light',
                    {'record_name': sign_request.title},
                    {'model_description': _('Service Agreement'), 'company': sign_request.create_uid.company_id},
                    {'email_from': sign_request.create_uid.email_formatted,
                        'author_id': sign_request.create_uid.partner_id.id,
                        'email_to': sign_request.signer_id.email_formatted,
                        'subject': sign_request.subject},
                    force_send=True,
                    lang=signer_lang,
                )
    
    def _message_send_mail(self, body, notif_template_xmlid, message_values, notif_values, mail_values, force_send=False, **kwargs):
        
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


    def sign_sa_action(self): 
            
        mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{self.create_uid.id}">@{self.create_uid.name}</a>'

        sales_order_link = _('<a href="#" data-oe-model="sale.order" data-oe-id="%(order_id)d">%(order_name)s</a>'
                        ) % {'order_id': self.sale_order_id.id, 'order_name': self.sale_order_id.name}

        message = _('Hello %(mention_html)s, the SA of %(order_link)s has been signed by the customer.'
                ) % {'order_link': sales_order_link, 'mention_html': mention_html}
              
        message = self.sale_order_id.message_post(
            body=message,
            partner_ids=[self.create_uid.partner_id.id],
            body_is_html = True
        )
        
        self.sale_order_id.message_notify(
            message_id=message.id,
        )
    def send_sa_to_customer(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        signer_lang = get_lang(self.env, lang_code=self.signer_id.lang).code
        
        body =  self.env['ir.ui.view'].with_context(lang=signer_lang)._render_template('pao_sign_sa.sa_template_fully_signed', 
            {
                'record': self,
                'link': url_join(base_url, '/sign/sa/%s/%s' % (self.id, self.access_token)),
                'subject': _('Fully Signed Service Agreement'),
                'body': False,
            }
        )
        self._message_send_mail(
            body, 'mail.mail_notification_light',
            {'record_name': self.title},
            {'model_description': _('Service Agreement'), 'company': self.create_uid.company_id},
            {'email_from': self.create_uid.email_formatted,
                'author_id': self.create_uid.partner_id.id,
                'email_to': self.signer_id.email_formatted,
                'subject': _('Fully Signed Service Agreement')},
            force_send=True,
            lang=signer_lang,
        )

    def regenerate_document(self):
        for rec in self:
            attachment_list = []
            for rn_sa in rec.registration_number_to_sign_ids:
                filename = "%s-%s.%s" % (rn_sa.name,rn_sa.organization_name, "pdf")
                #pdf = request.env.ref('pao_sign_sa.report_service_agreements').sudo()._render_qweb_pdf([sa_id.id], data= {"values": rn_sa, "print": True})[0]
                pdf = rec.env['ir.actions.report'].sudo()._render_qweb_pdf('pao_sign_sa.report_service_agreements', [rec.id], data= {"values": rn_sa, "print": True})[0]
                attachment = rec.env['ir.attachment'].sudo().create({
                        'name': filename,
                        'datas': base64.b64encode(pdf),
                        'res_model': 'pao.sign.sa.agreements.sent',
                        'res_id': rec.id,
                        'type': 'binary',  # override default_type from context, possibly meant for another model!
                    })
                attachment_list.append(attachment.id)
            
            rec.write({"attachment_ids": [(6, 0, attachment_list)]})
