from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    pao_currency_sa_id = fields.Many2one(
        'res.currency', 
        string='Currency in SA'
    )
    pao_product_price_sa = fields.Monetary(
        string="Product Price in SA",
        currency_field='pao_currency_sa_id',
        default=0
    )
    