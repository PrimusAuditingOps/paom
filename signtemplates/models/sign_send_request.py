from datetime import datetime, timedelta
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)
class SignSendRequest(models.TransientModel):
    _inherit = 'sign.send.request'

    st_mail_template_id = fields.Many2one(
        string='Mail Template',
        comodel_name='mail.template',
        domain = [('model','=','sign.request')],
    )
    st_reminder_days = fields.Integer(
        string = 'Reminder days',
        default = 0,
    )
    st_attachment_ids = fields.Many2many(
        string='Attachment',
        comodel_name='ir.attachment'
    )

    @api.onchange('st_mail_template_id')
    def _change_mail_template(self):
        self.message = self.st_mail_template_id.body_html
        self.subject = self.st_mail_template_id.subject
        self.st_attachment_ids = self.st_mail_template_id.attachment_ids

    def send_request(self):
        res = super(SignSendRequest, self).send_request()
        request = self.env['sign.request'].browse(res['context']['id'])
        request.st_mail_template_id = self.st_mail_template_id.id
        request.st_subject = self.subject
        request.st_reminder_days = self.st_reminder_days

        return res
    def create_request(self, send=True, without_mail=False):
        template_id = self.template_id.id
        if self.signers_count:
            signers = [{'partner_id': signer.partner_id.id, 'role': signer.role_id.id} for signer in self.signer_ids]
        else:
            signers = [{'partner_id': self.signer_id.id, 'role': False}]
        followers = self.follower_ids.ids
        reference = self.filename
        subject = self.subject
        message = self.message
        return self.env['sign.request'].initialize_new(template_id, signers, followers, reference, subject, message, send, without_mail, self.st_attachment_ids)