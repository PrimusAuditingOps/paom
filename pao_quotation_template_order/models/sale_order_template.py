from odoo import fields, models, api

class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    _order = "pao_sequence asc"


    pao_sequence = fields.Integer(
        string='Sequence', 
        default=10
    )