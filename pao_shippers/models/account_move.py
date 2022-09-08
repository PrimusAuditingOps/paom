from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit='account.move'

    pao_shipper_id = fields.Many2one(
        related='partner_id.pao_shipper_id',
    )