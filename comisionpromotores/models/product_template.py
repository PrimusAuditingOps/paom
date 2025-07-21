from odoo import fields, models, api



class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    pao_commission_payment = fields.Boolean(string='It is commission payment',
                                           default=False)
    