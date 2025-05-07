from odoo import fields, models, api



class PaoFixedPriceProduct(models.Model):
    _name = 'pao.fixed.price.product'
    _description = 'PAO Fixed Price Product'

    _sql_constraints = [
        ('uc_pao_fixed_price_product',
         'UNIQUE(product_template_id,partner_id,country_id)',
         "There is already a Vendor with this country"),
    ]

   
    partner_id = fields.Many2one(
        'res.partner', 
        string='Vendor', 
        ondelete='cascade', 
        required=True,
    )  
    price = fields.Float(
        string='Price', 
        default=0,
        required=True,
    )  
    country_id = fields.Many2one(
        'res.country', 
        string='Country', 
        ondelete='restrict', 
        required=True,
        default = lambda self: self.env.company.country_id.id,
    ) 
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency', 
        ondelete='restrict', 
        required=True,
        default = 2,
        readonly=True,
    ) 
    product_template_id = fields.Many2one(
        'product.template', 
        string='Product Template', 
        ondelete='cascade', 
    ) 