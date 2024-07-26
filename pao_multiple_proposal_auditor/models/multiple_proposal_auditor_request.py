from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from logging import getLogger
from datetime import datetime
from werkzeug.urls import url_join
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class MultipleProposalAuditorRequest(models.TransientModel):
    _name = 'multiple.proposal.auditor.request'
    _description = 'Multiple proposal auditor request'


    auditor_ids = fields.Many2many('res.partner', string="Auditores")
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
        domain = [('model','=','multiple.proposal.auditor.request')],
    )
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        ondelete='cascade',
    )
    @api.onchange('mail_template_id')
    def _change_mail_template(self):
        self.message = self.mail_template_id.body_html
        self.subject = self.mail_template_id.subject
        
    def send_multiple_proposal(self):
        self.ensure_one()

        """

        sa = self.env['pao.sign.sa.agreements.sent'].create({
            'signer_id': self.signer_id.id,
            'signer_email': self.signer_id.email,
            'position': self.position,
            'registration_numbers_ids': self.registration_numbers_ids,
            'sale_order_id': self.sale_order_id.id,
            'subject': self.subject,
            'message': self.message,
            'reminder_days': self.reminder_days,
            'follower_ids': self.follower_ids,

        })

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = url_join(base_url, '/sign/sa/%s/%s' % (sa.id, sa.access_token)),

        signer_lang = get_lang(self.env, lang_code=self.signer_id.lang).code
       
        for auditor in self.auditor_ids:
            auditor_lang = get_lang(self.env, lang_code=auditor.lang).code
            body =  self.env['ir.ui.view'].with_context(lang=auditor_lang)._render_template('pao_sign_sa.sa_template_mail_request_followers', 
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
                    'email_to': auditor.email_formatted,
                    'subject': self.subject},
                force_send=True,
                lang=auditor_lang,
            )

        """
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
