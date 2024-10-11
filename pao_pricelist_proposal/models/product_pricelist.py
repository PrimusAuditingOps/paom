from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductPriceList(models.Model):

    _name = 'product.pricelist'
    _inherit = ['product.pricelist', 'mail.thread', 'mail.activity.mixin']

    pricelist_proposal_id = fields.Many2one('pao.pricelist.proposal', string="Pricelist Proposal", readonly=True)
    pricelist_agreement_id = fields.Many2one('pao.pricelist.proposal', string="Pricelist Agreement", readonly=True)
    existing_proposal = fields.Boolean(string="Existing pricelist proposal", default=False)
            
    def create_pricelist_proposal(self):
        
        base_pricelist = self.env['product.pricelist'].search([], order='sequence', limit=1)
        
        pricelist_proposal = self.env['pao.pricelist.proposal']
        for record in self:
            proposal_values = {}
            proposal_values['name'] = _("Proposal") + " - " + record.name
            proposal_values['active'] = record.active
            proposal_values['company_id'] = record.company_id.id if record.company_id else False
            proposal_values['country_group_ids'] = [(6, 0, record.country_group_ids.ids)]
            proposal_values['currency_id'] = record.currency_id.id if record.currency_id else False
            proposal_values['discount_policy'] = record.discount_policy
            proposal_values['origin_product_pricelist_id'] = record.id
            proposal_values['base_url'] = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/pao_pricelist_proposal/static/src/img/pao_logo.png'
            proposal_values['base_pricelist'] = base_pricelist.id
            
            new_record = pricelist_proposal.create(proposal_values)
            
            items = []
            for line in getattr(record, 'item_ids'):
                item_values = {}
                for line_field_name, line_field in line._fields.items():
                    if line_field_name != 'id':
                        field_value = getattr(line, line_field_name)
                        if isinstance(line_field, fields.Many2one):
                            item_values[line_field_name] = field_value.id if field_value else False
                        else:
                            item_values[line_field_name] = field_value
                item_values['pricelist_id'] = new_record.id
                items.append((0, 0, item_values))
            new_record.item_ids = items
        
        self.pricelist_proposal_id = new_record.id
        self.existing_proposal = True

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pao.pricelist.proposal',
            'view_mode': 'form',
            'res_id': new_record.id,
            'target': 'current',
        }
        
    def action_view_existing_proposal(self):
        self.ensure_one()     
        action = {
            'res_model': 'pao.pricelist.proposal',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('pao_pricelist_proposal.pao_pricelist_proposal_view_form').id,
            'name': _("Pricelist Proposal"),
            'res_id': self.pricelist_proposal_id.id,
        }
        return action
    
    def action_view_pricelist_agreement(self):
        if self.pricelist_agreement_id:
            self.ensure_one()     
            action = {
                'res_model': 'pao.pricelist.proposal',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('pao_pricelist_proposal.pao_pricelist_proposal_view_form').id,
                'name': _("Pricelist Proposal"),
                'res_id': self.pricelist_agreement_id.id,
            }
            return action
    
    def notify_action(self, notification_message, attachment=None, manager_user = None):
        
        user = self.pricelist_proposal_id.create_uid if not manager_user else manager_user
        
        attachments = [attachment.id] if attachment else None
        
        message = self.message_post(
            body=notification_message,
            partner_ids=[user.partner_id.id],
            attachment_ids=attachments,
            body_is_html = True
        )
        
        self.message_notify(
            message_id=message.id,
        )
        
    def request_proposal_approval(self):
        
        pricelist_proposal_manager = self.env['hr.employee'].search([('pricelist_proposal_manager', '=', True)], limit=1)
        
        if not pricelist_proposal_manager:
            raise ValidationError(_("No employee in charge of pricelist proposals was found."))
        
        approver = pricelist_proposal_manager.user_id
        
        mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{approver.id}">@{approver.name}</a>'
        
        proposal_link = _('<a href="#" data-oe-model="pao.pricelist.proposal" data-oe-id="%(proposal_id)d">pricelist proposal</a>'
                        ) % {'proposal_id': self.pricelist_proposal_id.id}

        message = _('Hello %(mention_html)s,  your approval is required for this %(proposal_link)s to be shared with the client.'
                ) % {'proposal_link': proposal_link, 'mention_html': mention_html}
        
        self.notify_action(message, manager_user=approver)