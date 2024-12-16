from odoo import models, fields

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    is_travel_expenses = fields.Boolean(default=False, string="It's a travel expense")

