from odoo import api, fields, models, _
from datetime import datetime
from werkzeug.urls import url_join
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

class SendAnniversaryReminder(models.TransientModel):
    _name = 'send.anniversary.reminder'
    _description = 'Send Anniversary Reminder'

    email_address = fields.Char(string="Email Address", required=True)
    organization = fields.Char(string="Organization Name", required=True, readonly=True)
    registry_number = fields.Char(string="Organization Name", required=True, readonly=True)
    scheme = fields.Char(string="Scheme Name", required=True, readonly=True)
    subject = fields.Char(string="Subject", required=True)
    message = fields.Html(string="Message", required=True)
    anniversary_reminder_id = fields.Many2one('pao.anniversary.reminder', string="Reminder", readonly=True)
    language_id = fields.Many2one('res.lang', string="Language", required=True)
    
    mail_template_id = fields.Many2one(
        string='Mail Template',
        comodel_name='mail.template',
        domain = [('model','=','send.anniversary.reminder')],
        default = lambda self: self.env.ref('pao_anniversary_reminder.mail_template_anniversary_reminder')
    )
    
    @api.onchange('mail_template_id')
    def _set_mail_values(self):
        for record in self:
            if record.mail_template_id:
                
                template = record.mail_template_id
                
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                accept_link = url_join(base_url, '/anniversary_reminder/%s/%s?action=accept' % (record.anniversary_reminder_id.id, record.anniversary_reminder_id.access_token))
                reject_link = url_join(base_url, '/anniversary_reminder/%s/%s?action=reject' % (record.anniversary_reminder_id.id, record.anniversary_reminder_id.access_token))
                
                context = {'lang': self.language_id.code}
                
                raw_body = template.with_context(context).body_html
                raw_body = raw_body.replace("%7B", "{")
                raw_body = raw_body.replace("%7D", "}")
                
                rendered_body = raw_body.format(accept_link = accept_link, reject_link = reject_link, organization=record.organization, registry_number = record.registry_number)
                
                record.subject = record.mail_template_id.with_context(context).subject + ' ' + record.scheme +": " + record.organization
                record.message = rendered_body
                
                
    def send_mail(self):
        for record in self:
            if record.subject and record.message and record.organization and record.email_address:
                
                template = record.mail_template_id
                mail_values = {
                    'subject': record.subject,
                    'body_html': record.message,
                    'email_to': record.email_address,
                    'email_cc': template.email_cc,
                    'attachment_ids': template.attachment_ids
                }
                mail = self.env['mail.mail'].create(mail_values)
                mail.sudo().send()
                
                record.anniversary_reminder_id.attempt = record.anniversary_reminder_id.attempt + 1
                record.anniversary_reminder_id.status = 'contact_' + str(record.anniversary_reminder_id.attempt)
                
                message = _('Reminder #%(attempt)s sent.'
                        ) % {'attempt': record.anniversary_reminder_id.attempt}
                record.anniversary_reminder_id.notify_action(message)
                