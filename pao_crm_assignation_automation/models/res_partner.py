from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductPriceList(models.Model):

    _inherit = 'res.partner'

    def action_view_assignation_request(self):
        self.ensure_one()
        if self.company_id.country_code != 'US':
            raise ValidationError(_("This action is not available for your company."))
        
        tags = self.category_id.mapped('name')
        tags = [tag[0].upper() + tag[1:] for tag in tags]
        subject = self.name + ' - ' + (', '.join(tags))
        
        attachments = self.env["ir.attachment"].search([("res_model","=",'res.partner'), ("res_id","=",self.id)])
        
        assignation_note = self._get_assignation_notes()
        
        return {
            'name': 'Assignation Request',
            'type': 'ir.actions.act_window',
            'res_model': 'create.assignation.ticket',
            'view_mode': 'form',
            'view_id': self.env.ref('pao_crm_assignation_automation.create_assignation_ticket_view_form').id,
            'target': 'new',
            'context': {
                'default_body': assignation_note,
                'default_subject': subject,
                'default_partner_id': self.id,
                'default_attachment_ids': attachments.ids
            },
        }
        
    def _get_assignation_notes(self):
        
        messages = self.env['mail.message'].search([
            ('model', '=', 'res.partner'),
            ('res_id', '=', self.id),
        ])
        
        note = ""
        for message in messages:
            
            if "#assignation" in message.body.lower():
                
                message_body = message.body.replace("#Assignation", "")
                message_body = message_body.replace("#assignation", "")
                note += _('Note by %(author)s: %(message)s</br>'
                    ) % {'author': message.author_id.name, 'message': message_body}
                
        return note