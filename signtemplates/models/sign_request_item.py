from werkzeug.urls import url_join
import logging

from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SignRequestItemInh(models.Model):
    _inherit = 'sign.request.item'

    def send_signature_accesses(self, subject=None, message=None):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for signer in self:
            if not signer.partner_id or not signer.partner_id.email:
                continue
            if not signer.create_uid.email:
                continue
            tpl = self.env.ref('sign.sign_template_mail_request')
            if signer.partner_id.lang:
                tpl = tpl.with_context(lang=signer.partner_id.lang)
            body = tpl._render({
                'record': signer,
                'link': url_join(base_url, "sign/document/mail/%(request_id)s/%(access_token)s" % {'request_id': signer.sign_request_id.id, 'access_token': signer.access_token}),
                'subject': subject,
                'body': message if message != '<p><br></p>' else False,
            }, engine='ir.qweb', minimal_qcontext=True)
            if not signer.signer_email:
                raise UserError(_("Please configure the signer's email address"))
            self.env['sign.request']._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': signer.sign_request_id.reference},
                {'model_description': 'signature', 'company': signer.create_uid.company_id},
                {'email_from': formataddr((signer.create_uid.name, signer.create_uid.email)),
                 'author_id': signer.create_uid.partner_id.id,
                 'email_to': formataddr((signer.partner_id.name, signer.partner_id.email)),
                 'subject': subject,
                 'attachment_ids':  [(6, 0, signer.sign_request_id.attachment_ids.ids)] },
                force_send=True
            )