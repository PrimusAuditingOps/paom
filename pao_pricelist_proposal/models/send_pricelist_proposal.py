from odoo import api, fields, models, _
from werkzeug.urls import url_join

class SendPricelistProposal(models.TransientModel):
    _name = 'send.pricelist.proposal'
    _description = 'Pricelist send proposal'

    customer_ids = fields.Many2many('res.partner', string="Customer",required=True)
    subject = fields.Char(string="Subject", required=True)
    message = fields.Html(string="Message", required=True)
    pricelist_proposal_id = fields.Many2one('pao.pricelist.proposal', string="Pricelist Proposal", readonly=True)
    proposal_terms =  fields.Many2one('proposal.terms.schemes', string="Terms & Conditions", required=True)
    message_proposal_template_id = fields.Many2one('proposal.templates', string="Template", required=True)
    
    mail_template_id = fields.Many2one(
        string='Mail Template',
        comodel_name='mail.template',
        domain = [('model','=','send.pricelist.proposal')],
        default = lambda self: self.env.ref('pao_pricelist_proposal.mail_template_pricelist_proposal')
    )
    
    @api.onchange('mail_template_id', 'customer_ids', 'message_proposal_template_id')
    def _set_mail_values(self):
        for record in self:
            if record.mail_template_id:
                
                lang = record.pricelist_proposal_id.create_uid.lang
                
                template = self.env.ref('pao_pricelist_proposal.mail_template_pricelist_proposal')
                
                
                customer_lang = self.customer_ids[0].lang if self.customer_ids else self.pricelist_proposal_id.create_uid.lang
                context = {'lang': customer_lang}
                
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                link = url_join(base_url, '/pricelist_proposal/%s/%s' % (record.pricelist_proposal_id.id, record.pricelist_proposal_id.access_token))
                
                customer_name = ", ".join(self.customer_ids.mapped("display_name")) if record.customer_ids else '____________'
                specialist = record.pricelist_proposal_id.create_uid.name
                message_proposal_template = record.message_proposal_template_id.with_context(context).template if record.message_proposal_template_id else '________________________'
                
                mail_body_html = template.with_context(context).body_html
                
                mail_body_html = mail_body_html.replace("%7B", "{")

                mail_body_html = mail_body_html.replace("%7D", "}")
                
                rendered_body = mail_body_html.format(proposal_link = link, customer_name=customer_name, specialist=specialist, message_proposal_template=message_proposal_template)
                
                record.subject = record.mail_template_id.with_context(context).subject + " " + record.pricelist_proposal_id.origin_product_pricelist_id.name
                record.message = rendered_body
                
                
    def send_mail(self):
        for record in self:
            if record.subject and record.message and record.customer_ids:
                
                customer_emails = ', '.join([customer.email_formatted for customer in record.customer_ids])
                
                mail_values = {
                    'subject': record.subject,
                    'body_html': record.message,
                    'email_to': customer_emails,
                    'attachment_ids': record.message_proposal_template_id.attachment_ids
                }
                mail = self.env['mail.mail'].create(mail_values)
                mail.send()
                record.pricelist_proposal_id.proposal_status = 'sent'
                record.pricelist_proposal_id.customer_ids = self.customer_ids
                record.pricelist_proposal_id.proposal_terms = self.proposal_terms.id
                record.pricelist_proposal_id.message_proposal_template_id = self.message_proposal_template_id.id
                