from odoo import fields, models, api



class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    can_be_commissionable = fields.Boolean(string='Can be Commissionable',
                                           default=False)
    
    pao_fixed_price_in_dollars = fields.Boolean(string='It is a fixed price for the vendor',
                                           default=False)

    pao_fixed_price_product_ids = fields.One2many('pao.fixed.price.product',
                                         inverse_name='product_template_id',
                                         string='Products')