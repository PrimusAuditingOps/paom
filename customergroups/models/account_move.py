from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit='account.move'

    cgg_customer_group = fields.Many2one(
        related='partner_id.cgg_group_id',
    )