from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductCategoryExpense(models.Model):
    _inherit = 'product.product'
    
    category_for_auditors = fields.Boolean(string="Category available for auditors", default=False)
