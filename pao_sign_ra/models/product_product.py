from odoo import models, fields

class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    is_travel_expenses = fields.Boolean(default=False, string="It's a travel expense")

