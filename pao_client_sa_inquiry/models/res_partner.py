from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartnerInherit(models.Model):

    _inherit="res.partner"
    
    pao_agreements_ids = fields.One2many(
        comodel_name='pao.sign.sa.agreements.sent',
        inverse_name='signer_id',
        compute='_compute_agreements',
        string='Agrements',
    )
    
    pao_agrements_count = fields.Integer(
        compute='_compute_agreements'
    )
    
    @api.depends('pao_agreements_ids')
    def _compute_agreements(self):
        for record in self:
            related_agreements = record.env['pao.sign.sa.agreements.sent'].search([('signer_id', 'in', [record.id] + record.child_ids.ids), ('document_status', '!=', 'cancel' )])
            record.pao_agreements_ids = related_agreements
            record.pao_agrements_count = len(record.pao_agreements_ids)
            
    def action_view_partner_service_agreements(self):
        self.ensure_one()     
        action = {
            'res_model': 'pao.sign.sa.agreements.sent',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _("Service Agreements - %s", self.display_name),
            'domain': [('id', 'in', self.pao_agreements_ids.ids)],
            'context': {
                'display_sale_order': True,
            }
        }
        return action