from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from logging import getLogger
from datetime import datetime
from werkzeug.urls import url_join
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class SASendRequest(models.TransientModel):
    _name = 'sa.send.request'
    _description = 'Service Agreement send request'


    signer_id = fields.Many2one(
        'res.partner', 
        string="Signer",
        required=True,
    )
    follower_ids = fields.Many2many('res.partner', string="Copy to")
    position = fields.Char(
        string="Position", 
        required=True
    )
    registration_numbers_ids = fields.Many2many(
        'servicereferralagreement.registrynumber', 
        string="Registration Numbers",
        required=True,
    )
    subject = fields.Char(
        string="Subject", 
        required=True
    )

    message = fields.Html(
        string="Message",
    )
    mail_template_id = fields.Many2one(
        string='Mail Template',
        comodel_name='mail.template',
        domain = [('model','=','sa.send.request')],
    )
    reminder_days = fields.Integer(
        string = 'Reminder days',
        default = 0,
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        ondelete='cascade',
    )
    enable_registration_numbers_ids = fields.Many2many(
        related="sale_order_id.pao_registration_numbers_ids",
    )
    @api.onchange('mail_template_id')
    def _change_mail_template(self):
        self.message = self.mail_template_id.body_html
        self.subject = self.mail_template_id.subject

    
    def _validate_fields_sa(self):
        for rn in self.registration_numbers_ids:

            orderLine = filter(lambda x: x['registrynumber_id'].id == rn.id, self.sale_order_id.order_line)
            msg = ""
            for line in orderLine:
                if not line.service_end_date or not line.service_start_date:
                    msg=_("Please enter a date for service of the registration number ")
                    raise ValidationError(msg + rn.name)
                if rn.scheme_id.name in ["PrimusGFS", "Primus Standard GMP", "Primus Standard GAP", "NOP", "SMETA"]:
                    if not line.coordinator_id.name:
                        msg=_("Please select a coordinator for service of the registration number ")
                        raise ValidationError(msg + rn.name)
                    if not line.coordinator_id.employee_id.es_sign_signature:
                        msg=_("The coordinator doesn't have a signature, please assign a signature for the coordinator ")
                        raise ValidationError(msg + line.coordinator_id.name)

            if rn.scheme_id.name in ["PrimusGFS", "Primus Standard GMP", "Primus Standard GAP", "NOP", "SMETA"]:
                if not self.sale_order_id.partner_id.vat: 
                    msg=_("Please enter a VAT for the customer.")
                    raise ValidationError(msg)
                if not rn.contract_email: 
                    msg=_("Please enter a contract E-mail for the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.phone: 
                    msg=_("Please enter a phone for the registration number ")
                    raise ValidationError(msg + rn.name)
                if not self.sale_order_id.partner_id.email: 
                    msg=_("Please enter a E-mail for the customer.")
                    raise ValidationError(msg)
            
            if rn.scheme_id.name in ["GLOBALG.A.P.", "NOP-LPO", "HACCP", "LPO-UE"]:
                if not rn.organization_id.rfc: 
                    msg=_("Please enter a vat for organization of the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.organization_id.address: 
                    msg=_("Please enter an address for organization of the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.organization_id.city: 
                    msg=_("Please enter a city for organization of the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.organization_id.state_id.name: 
                    msg=_("Please enter a state for organization of the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.organization_id.country_id.name: 
                    msg=_("Please enter a country for organization of the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.type_of_audit: 
                    msg=_("Please enter a type of audit for the registration number ")
                    raise ValidationError(msg + rn.name)
            if rn.scheme_id.name in ["LPO-UE"]:
                if not rn.audit_scope: 
                    msg=_("Please enter an audit scope for the registration number ")
                    raise ValidationError(msg + rn.name)
            if rn.scheme_id.name == "SMETA":
                if not rn.client_requirements: 
                    msg=_("Please enter client requirements for the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.audit_duration: 
                    msg=_("Please enter an audit duration for the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.organization_id.rfc: 
                    msg=_("Please enter a vat for organization of the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.type_of_audit: 
                    msg=_("Please enter a type of audit for the registration number ")
                    raise ValidationError(msg + rn.name)
                if not rn.audit_scope: 
                    msg=_("Please enter an audit scope for the registration number ")
                    raise ValidationError(msg + rn.name)
        
    def send_request(self):
        self.ensure_one()
        self._validate_fields_sa()
        zone = self.env.user.tz
        requested_tz = pytz.timezone(zone)
        today = requested_tz.fromutc(datetime.utcnow())

        sa = self.env['pao.sign.sa.agreements.sent'].create({
            'signer_id': self.signer_id.id,
            'signer_email': self.signer_id.email,
            'position': self.position,
            'registration_numbers_ids': self.registration_numbers_ids,
            'sale_order_id': self.sale_order_id.id,
            'subject': self.subject,
            'message': self.message,
            'document_date': today,
            'reminder_days': self.reminder_days,
            'follower_ids': self.follower_ids,

        })
        for registration_number in self.registration_numbers_ids:
            
            start_date = ""
            end_date = ""
            productname = ""
            products = []
            coordinator = 0
            orderLine = filter(lambda x: x['registrynumber_id'].id == registration_number.id, self.sale_order_id.order_line)
            services = []
            
            for line in orderLine:
                for prod in line.audit_products:
                    if prod.id not in products:
                        productname += prod.name if productname == "" else ", " + prod.name
                        products.append(prod.id)

                if line.service_start_date:
                    start_date = line.service_start_date
                    end_date = line.service_end_date
                if line.coordinator_id:
                    coordinator = line.coordinator_id.id
                service = self.env['pao.registration.number.services'].create({
                    'name': line.name,
                    'product_uom_qty': line.product_uom_qty,
                    'currency_id': self.sale_order_id.currency_id.id,
                    'price_subtotal': line.price_subtotal,
                })
                services.append(service.id)  


            rn = self.env['pao.registration.number.to.sign'].create({
                'name': registration_number.name,
                'scheme': registration_number.scheme_id.name,
                'version': registration_number.version_scheme,
                'customer_name': self.sale_order_id.partner_id.name,
                'customer_vat': self.sale_order_id.partner_id.vat,
                'phone': registration_number.phone,
                'contract_email': registration_number.contract_email,
                'invoice_email': self.sale_order_id.partner_id.email,
                'organization_name': registration_number.organization_id.name,
                'organization_vat': registration_number.organization_id.rfc,
                'organization_address': registration_number.organization_id.address,
                'organization_city': registration_number.organization_id.city,
                'organization_state': registration_number.organization_id.state_id.name,
                'organization_country': registration_number.organization_id.country_id.name,
                'start_date': start_date,
                'end_date': end_date,
                'currency_id': self.sale_order_id.currency_id.id,
                'audit_type': registration_number.type_of_audit,
                'audit_scope': registration_number.audit_scope,
                'products': productname,
                'client_requirements': registration_number.client_requirements,
                'audit_duration': registration_number.audit_duration,
                'coordinator_id': coordinator,
                'sign_sa_agreements_id': sa.id,
                'services_ids': [(6, 0, services)],
            })
        rn_sent = []
        for rec in sa.registration_number_to_sign_ids:
            sa_sent = []
            sa_sent += [r.id for r in self.sale_order_id.pao_agreements_ids]
            rec_rn = self.env['pao.registration.number.to.sign'].search([("sign_sa_agreements_id", "in", sa_sent), ("id", "!=", rec.id),('name','ilike',rec.name)], limit=1, order='create_date desc')
            for r in rec_rn:
                rn_sent.append(r)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        signer_lang = get_lang(self.env, lang_code=self.signer_id.lang).code
        body =  self.env['ir.ui.view'].with_context(lang=signer_lang)._render_template('pao_sign_sa.sa_template_mail_request', 
            {
                'record': sa,
                'rnsent': rn_sent,
                'link': url_join(base_url, '/sign/sa/%s/%s' % (sa.id, sa.access_token)),
                'subject': self.subject,
                'body': self.message if self.message != '<p><br></p>' else False,
            }
        )
        sa.write({'sign_url': url_join(base_url, '/sign/sa/%s/%s' % (sa.id, sa.access_token))})
        
        mail = self._message_send_mail(
            body, 'mail.mail_notification_light',
            {'record_name': sa.title},
            {'model_description': _('Service Agreement'), 'company': self.create_uid.company_id},
            {'email_from': self.create_uid.email_formatted,
                'author_id': self.create_uid.partner_id.id,
                'email_to': self.signer_id.email_formatted,
                'subject': self.subject},
            force_send=True,
            lang=signer_lang,
        )
        if mail:
            sa.write({'mail_id': mail.id})
            for follower in self.follower_ids:
                follower_lang = get_lang(self.env, lang_code=follower.lang).code
                body =  self.env['ir.ui.view'].with_context(lang=follower_lang)._render_template('pao_sign_sa.sa_template_mail_request_followers', 
                    {
                        'record': sa,
                        'subject': self.subject,
                        'body': self.message if self.message != '<p><br></p>' else False,
                    }
                )


                mail = self._message_send_mail(
                    body, 'mail.mail_notification_light',
                    {'record_name': sa.title},
                    {'model_description': _('Service Agreement'), 'company': self.create_uid.company_id},
                    {'email_from': self.create_uid.email_formatted,
                        'author_id': self.create_uid.partner_id.id,
                        'email_to': follower.email_formatted,
                        'subject': self.subject},
                    force_send=True,
                    lang=follower_lang,
                )
        else:
            sa.write({'document_status': 'exception'})

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
