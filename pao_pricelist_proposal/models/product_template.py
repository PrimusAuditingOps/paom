from odoo import models, fields
from odoo.exceptions import ValidationError

class ProductTemplateInherit(models.Model):

    _inherit = 'product.template'
    
    name = fields.Char(copy=False)