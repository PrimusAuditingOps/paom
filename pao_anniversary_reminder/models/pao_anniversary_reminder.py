from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
import pytz, json
import uuid
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from werkzeug.urls import url_join

class PaoAnniversaryReminder(models.Model):

    _name="pao.anniversary.reminder"
    _description = "Anniversary reminder to customers"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Name', readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', string="Order Reference", readonly=True)
    organization_id = fields.Many2one('servicereferralagreement.organization', string="Organization", readonly=True)
    registrynumber_id = fields.Many2one('servicereferralagreement.registrynumber', string="Registry Number", readonly=True)
    service_start_date = fields.Date("Service Start Date", readonly=True)
    email_address = fields.Char("Email Address")
    status = fields.Selection(default="pending", selection=[
        ('pending', 'Pending'),
        ('contact_1', '1st Contact'),
        ('contact_2', '2nd Contact'),
        ('contact_3', '3rd Contact'),
        ('progress', 'In Progress'),
        ('confirm', 'Confirmed'),
        ('lost', 'Lost'),
    ])
    language_id = fields.Many2one('res.lang', string="Language", required=True)
    
    observations = fields.Text("Observations", readonly=True)
    
    attempt = fields.Integer('Contact Attempt', default=0, readonly=True)
    
    reminder_sender_id = fields.Many2one('res.users', string='Sender')
    
    scheme_name = fields.Char(string="Scheme")
    
    access_token = fields.Char(
        'Access Token', 
        default=lambda self: self._get_access_token(),
        copy=False,
        readonly=True
    )
            
    @api.model
    def _get_access_token(self):
        return uuid.uuid4().hex
    
    def _set_reminder_language(self, country_code):
        if country_code == 'US':
            return self.env['res.lang'].search([('code', '=', 'en_US')], limit=1)
        else:
            return self.env['res.lang'].search([('code', '=', 'es_MX')], limit=1)
    
    def _get_today_date(self):
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        return today.date()
    
    def send_mass_reminders(self):
        for record in self:
            if record.registrynumber_id and record.organization_id and record.attempt < 3 and record.status not in ('progress', 'confirm', 'lost'):
                
                record.reminder_sender_id = self.env.user
                
                if record.attempt == 0:
                    record.access_token = record._get_access_token()
                
                template = self.env.ref('pao_anniversary_reminder.mail_template_anniversary_reminder')
                
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                accept_link = url_join(base_url, '/anniversary_reminder/%s/%s?action=accept' % (record.id, record.access_token))
                reject_link = url_join(base_url, '/anniversary_reminder/%s/%s?action=reject' % (record.id, record.access_token))
                
                context = {'lang': self.language_id.code}
                
                raw_body = template.with_context(context).body_html
                raw_body = raw_body.replace("%7B", "{")
                raw_body = raw_body.replace("%7D", "}")
                
                rendered_body = raw_body.format(accept_link = accept_link, reject_link = reject_link, organization=record.organization_id.name, registry_number = record.registrynumber_id.name)
                
                subject = template.with_context(context).subject + ' ' + record.scheme_name +": " + record.organization_id.name
                message = rendered_body
                
                mail_values = {
                    'subject': subject,
                    'body_html': message,
                    'email_to': record.email_address,
                }
                mail = self.env['mail.mail'].create(mail_values)
                mail.sudo().send()
                
                record.attempt = record.attempt + 1
                record.status = 'contact_' + str(record.attempt)
                
                message = _('Reminder #%(attempt)s sent.'
                        ) % {'attempt': record.attempt}
                record.notify_action(message)
                
                title = _("Successfully!")
                message = _("Reminders have been sent.")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': title,
                        'message': message,
                        'sticky': False,
                    }
                }
    
    def send_reminder_action(self):
        if self.registrynumber_id and self.organization_id and self.attempt < 3 and self.status not in ('confirm', 'lost'):
            
            self.reminder_sender_id = self.env.user
            
            if self.attempt == 0:
                self.access_token = self._get_access_token()
            
            return {
                'name': _('Send reminder'),
                'type': 'ir.actions.act_window',
                'res_model': 'send.anniversary.reminder',
                'view_mode': 'form',
                'view_id': self.env.ref('pao_anniversary_reminder.send_anniversary_reminder_view_form').id,
                'target': 'new',
                'context': {
                    'default_anniversary_reminder_id': self.id,
                    'default_organization': self.organization_id.name,
                    'default_registry_number': self.registrynumber_id.name,
                    'default_scheme': self.scheme_name,
                    'default_email_address': self.email_address,
                    'default_language_id': self.language_id.id
                },
            }
    
    def confirm_audit(self):
        if self.status == 'progress':
            self.status = 'confirm'
        
    def accept_audit(self, customer_observations=None):
        if self.attempt > 0:
            self.observations = customer_observations
            
            mention_html = f'<a href="/web#model=res.users&amp;id={self.reminder_sender_id.id}" class="o_mail_redirect" data-oe-id="{self.reminder_sender_id.id}" data-oe-model="res.users" target="_blank">@{self.reminder_sender_id.name}</a>'
    
            observations = '<b>' + (_(' and provided the following comments: ') + customer_observations +'</b>') if customer_observations else ''
            
            message = _('Hello %(mention_html)s, the customer has accepted the offer to schedule their audit%(observations)s. Please contact them to specify the details'
                        ) % {'mention_html': mention_html, 'observations': observations}
            
            self.status = 'progress'
            self.notify_action(message)
    
    def decline_audit(self, observations=''):
        if self.attempt > 0:
            self.observations = observations
            
            mention_html = f'<a href="/web#model=res.user&amp;id={self.reminder_sender_id.id}" class="o_mail_redirect" data-oe-id="{self.reminder_sender_id.id}" data-oe-model="res.users" target="_blank">@{self.reminder_sender_id.name}</a>'
            
            reasons = ('<br/><b>%(refuse_reason)s</b>') % {'refuse_reason': observations}
        
            message = _('Hello %(mention_html)s, the customer has rejected the offer to schedule their audit due to the following reasons: %(reasons)s'
                        ) % {'mention_html': mention_html, 'reasons': reasons}
            
            self.status = 'lost'
            self.notify_action(message)
            

    def notify_action(self, message, attachment=None):
        user = self.reminder_sender_id
        
        attachments = [attachment.id] if attachment else None
        
        message = self.message_post(
            body=message,
            partner_ids=[user.partner_id.id],
            attachment_ids=attachments,
            body_is_html = True
        )
        
        self.message_notify(
            message_id=message.id,
        )
        
            
    def get_customers_to_remind(self, date=None):
        
        if not date:
            date = self._get_today_date() - relativedelta(months=9)

        domain = [
            ('registrynumber_id', '!=', False), 
            ('organization_id', '!=', False), 
            ('state', '!=', 'cancel'),
            ('service_start_date', '=', date)
        ]
        
        purchase_order_lines = self.env['purchase.order.line'].search(domain)
        
        registry_numbers = []

        for line in purchase_order_lines:
            
            if line.registrynumber_id.id not in registry_numbers:
            
                registry_numbers.append(line.registrynumber_id.id)
                
                new_anniversary_reminder = self.create({
                    'organization_id': line.organization_id.id,
                    'registrynumber_id': line.registrynumber_id.id,
                    'name': line.organization_id.name + ' - ' +line.registrynumber_id.name,
                    'service_start_date': line.service_start_date,
                    'email_address': (line.registrynumber_id.contract_email).strip(),
                    'status': 'pending',
                    'language_id': self._set_reminder_language(line.organization_id.country_id.code).id,
                    'purchase_order_id': line.order_id.id,
                    'scheme_name': line.registrynumber_id.scheme_id.name
                })
        
        odoo_bot = self.env.ref('base.partner_root')
        
        number_reminders = len(registry_numbers)
        if number_reminders > 0:
            message=_('%(number_reminders)s reminders have been added today.') % {'number_reminders': number_reminders}
            channel = self.env['discuss.channel'].search([('name', 'ilike', 'Aniversarios')], limit=1) 
            if channel:
                channel.sudo().message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment', author_id=odoo_bot.id)
                    
    
    def change_status_action(self):
        status_change = self.env.context.get('status_change', False)
        self.status = status_change
        