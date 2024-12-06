from odoo import api, fields, models, _
from datetime import datetime

class CreateAssignationTicker(models.TransientModel):
    _name = 'create.assignation.ticket'
    _description = 'Create Asignation Ticket'

    subject = fields.Char(string="Subject", required=True, default=" ")
    body = fields.Html('Contents', default='', sanitize_style=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'create_assignation_ticket_ir_attachments_rel',
        'wizard_id', 'attachment_id', 'Attachments')
    
    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True,
        domain="[('model', '=', model)]")
    
    partner_id = fields.Many2one(
        'res.partner', 
        string="Partner",
    )
    
    def create_ticket(self):
        for record in self:
            partnert_id = 0
            user = self.env["res.users"].search([("id","=",record._uid)])
            for u in user:
                partner_id = u.partner_id.id
            
            heldesk_team_id = self.env["helpdesk.team"].search([("name", "ilike", 'Assignations')])
            
            heldesk_team_id = 1 if not heldesk_team_id else heldesk_team_id.id
            
            ticket_attrs = {'name': record.subject,'partner_id':partner_id,'team_id':heldesk_team_id} 
            
            ticket = self.env['helpdesk.ticket'].sudo().create(ticket_attrs)
            
            if self.body or self.attachment_ids:
                ticket.message_post(
                    body=self.body if self.body else '',
                    attachment_ids = self.attachment_ids.ids,
                    body_is_html = True
                )
            
            ticket_link = _('<a href="#" data-oe-model="helpdesk.ticket" data-oe-id="%(ticket_id)d">Assignation request</a>'
                            ) % {'ticket_id': ticket.id}
            
            message = _('%(ticket_link)s created.'
                    ) % {'ticket_link': ticket_link}
            
            record.partner_id.message_post(
                body=message,
                body_is_html = True
            )
            
    # @api.onchange('subject')
    # def _set_ticket_values(self):
    #     for record in self:
            
    #         # tags = record.tags_id.mapped('name')
    #         # record.subject = record.partner_id.name + '-' + tags
    #         record.body = "Hi, Could you help me with this Assignation? Best Regards."
                
    #         # lang = record.pricelist_proposal_id.create_uid.lang
            
    #         # template = self.env.ref('pao_pricelist_proposal.mail_template_pricelist_proposal')
            
    #         # customer_lang = self.customer_id.lang if self.customer_id else self.pricelist_proposal_id.create_uid.lang
    #         # context = {'lang': customer_lang}
            
    #         # message_proposal_template = record.message_proposal_template_id.with_context(context).template if record.message_proposal_template_id else '________________________'
            
    #         # rendered_body = template.with_context(context).body_html.format(proposal_link = link, customer_name=customer_name, specialist=specialist, message_proposal_template=message_proposal_template)
            
    #         # record.subject = record.mail_template_id.with_context(context).subject + " " + record.pricelist_proposal_id.origin_product_pricelist_id.name
                
                
    