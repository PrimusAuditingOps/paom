from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class SaleOrder(models.Model):

    _inherit='sale.order'
    
    
    pao_agreements_ids = fields.One2many(
        comodel_name='pao.sign.sa.agreements.sent',
        inverse_name='sale_order_id',
        string='Agrements',
    )

    pao_agrements_count = fields.Integer(
        compute='_get_agreements'
    )

    pao_registration_numbers_ids = fields.Many2many(
        comodel_name='servicereferralagreement.registrynumber',
        compute='_get_registration_numbers', 
        string='Registration numbers',
        readonly=True,
    )   


    @api.depends('pao_agreements_ids')
    def _get_agreements(self):
        for order in self:
            order.pao_agrements_count = len(order.pao_agreements_ids)

    @api.depends('order_line')
    def _get_registration_numbers(self):
        for rec in self:
            listnumbers = []

            for line in rec.order_line:
                if line.registrynumber_id:
                    if line.registrynumber_id.id not in listnumbers:
                            listnumbers.append(line.registrynumber_id.id) 
            rec.pao_registration_numbers_ids = listnumbers
    
    def action_view_service_agreements(self):
        self.ensure_one()     
        action = {
            'res_model': 'pao.sign.sa.agreements.sent',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _("Service Agreements - %s", self.name),
            'domain': [('sale_order_id', '=', self.id)],
        }
        return action