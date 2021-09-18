
from datetime import datetime, timedelta
import logging
import re
import dateutil.parser
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class sign_request(models.Model):
    _inherit = 'sign.request'

    st_mail_template_id = fields.Many2one(
        string='Mail Template',
        comodel_name='mail.template',
    )
    st_reminder_days = fields.Integer(
        string = 'Reminder days',
        default = 0,
    )
    attachment_ids = fields.Many2many(
        string='Attachment',
        comodel_name='ir.attachment'
    )
    st_subject = fields.Char(
        string='Subject'
    )
    @api.model
    def _message_send_mail(self, body, notif_template_xmlid, message_values, notif_values, mail_values, force_send=False, **kwargs):
        """ Shortcut to send an email. """
        # the notif layout wrapping expects a mail.message record, but we don't want
        # to actually create the record
        # See @tde-banana-odoo for details

        if 'attachment_ids' in mail_values.keys():
            attach_ids = []
            for attachment_data in mail_values['attachment_ids']:
                if attachment_data[0] == 6:
                    for attachment in self.env['ir.attachment'].browse(attachment_data[2]):
                        if not re.match(r'.*activity logs.*', attachment.name.lower()):
                            attach_ids.append(attachment.id)
                if attachment_data[0] == 4:
                    attachment = self.env['ir.attachment'].browse([attachment_data[1]])
                    if not re.match(r'.*activity logs.*', attachment.name.lower()):
                        attach_ids.append(attachment.id)
            mail_values['attachment_ids'] = [(6, 0, attach_ids)]
        msg = self.env['mail.message'].sudo().new(dict(body=body, **message_values))
        
        notif_layout = self.env.ref(notif_template_xmlid)
        body_html = notif_layout._render(dict(message=msg, **notif_values), engine='ir.qweb', minimal_qcontext=True)
        body_html = self.env['mail.render.mixin']._replace_local_links(body_html)

        mail = self.env['mail.mail'].create(dict(body_html=body_html, state='outgoing', **mail_values))
        if force_send:
            mail.send()
        return mail

    @api.model
    def initialize_new(self, id, signers, followers, reference, subject, message, 
    send=True, without_mail=False, attachment_ids=False):
        sign_users = self.env['res.users'].search([('partner_id', 'in', [signer['partner_id'] for signer in signers])]).filtered(lambda u: u.has_group('sign.group_sign_user'))
        sign_request = self.create({'template_id': id, 'reference': reference, 'favorited_ids': [(4, item) for item in (sign_users | self.env.user).ids]})
        sign_request.message_subscribe(partner_ids=followers)
        sign_request.activity_update(sign_users)
        sign_request.set_signers(signers)
        sign_request.attachment_ids = attachment_ids
        if send:
            sign_request.action_sent(subject, message)
        if without_mail:
            sign_request.action_sent_without_mail()
        return {
            'id': sign_request.id,
            'token': sign_request.access_token,
            'sign_token': sign_request.request_item_ids.filtered(lambda r: r.partner_id == self.env.user.partner_id)[:1].access_token,
        }
    @api.model
    def _send_signature_reminders(self):
        for sign_request_item in self.env['sign.request.item'].search([('state', '=', 'sent')]):
            request = sign_request_item.sign_request_id
            create_date = request.create_date

            if not create_date:
                continue

            request.st_reminder_days
            
            if request.st_reminder_days <= 0:
                continue

            today = datetime.now().date()
            reminder = create_date + timedelta(days=request.st_reminder_days)
            reminder = dateutil.parser.parse(str(reminder)).date()
            _logger.error("fecha hoy: " + str(today) )
            _logger.error("fecha reminder: " + str(reminder) )

            if today > reminder:
                continue

            template = request.st_mail_template_id
            subject = request.st_subject
            body = template.body_html if template.id else None
            sign_request_item.send_signature_accesses(subject=subject, message=body)