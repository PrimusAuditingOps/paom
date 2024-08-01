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


    auditor_ids = fields.Many2many('res.partner', string="Auditores", domain=[("ado_is_auditor","=", True)])
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
    range_start_date = fields.Date(string="Range start date", required=True)
    range_end_date = fields.Date(string="Range end date", required=True)
    @api.onchange('mail_template_id')
    def _change_mail_template(self):
        self.message = self.mail_template_id.body_html
        self.subject = self.mail_template_id.subject
        
    def send_multiple_proposal(self):
        self.ensure_one()
        
        auditor_response_vals = []
        for r in self.auditor_ids:
            auditor_response_vals.append({"auditor_id": r.id, "status": 'pending', "purchase_id": self.purchase_order_id.id})
        
        self.env["auditor.response.multi.proposal"].create(auditor_response_vals)
        self.purchase_order_id.write(
            {
                "audit_status_muilti_proposal": 'sent', 
                "multi_proposal_range_start_date": self.range_start_date, 
                "multi_proposal_range_end_date": self.range_end_date
            }
        )
        self.purchase_order_id._portal_ensure_token()


       
        for auditor in self.auditor_ids:
            auditor_lang = get_lang(self.env, lang_code=auditor.lang).code
            body =  self.env['ir.ui.view'].with_context(lang=auditor_lang)._render_template('pao_multiple_proposal_auditor.pao_multiple_proposal_auditor_template_mail', 
                {
                    'link': '/multiple/proposal/%s/%s' % (self.purchase_order_id.id, self.purchase_order_id.access_token),
                    'auditor_name': auditor.name,
                    'body': self.message if self.message != '<p><br></p>' else False,
                }
            )


            mail = self._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': ''},
                {'model_description': _('Audit proposal'), 'company': self.create_uid.company_id},
                {'email_from': self.create_uid.email_formatted,
                    'author_id': self.create_uid.partner_id.id,
                    'email_to': auditor.email_formatted,
                    'subject': self.subject},
                force_send=True,
                lang=auditor_lang,
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
