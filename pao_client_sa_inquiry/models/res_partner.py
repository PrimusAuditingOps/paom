from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartnerInherit(models.Model):

    _inherit="res.partner"
    
    pao_agreements_ids = fields.One2many(
        comodel_name='pao.sign.sa.agreements.sent',
        inverse_name='so_partner_id',
        compute='_compute_agreements',
        string='Agrements',
    )
    
    @api.depends('pao_agreements_ids')
    def _compute_agreements(self):
        for record in self:
            related_greemetns = record.env['pao.sign.sa.agreements.sent'].search([('so_partner_id', 'in', [record.id] + record.child_ids.ids)])
            record.pao_agreements_ids = related_greemetns

    
    