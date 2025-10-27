from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pao_is_module_9 = fields.Boolean(default=False, string="It's Module 9")

