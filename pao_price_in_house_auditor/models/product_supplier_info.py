from odoo import fields, models, api

class ProductSupplierInfor(models.Model):
    _inherit='product.supplierinfo'

    pao_is_an_in_house_auditor = fields.Boolean(realated="partner_id.is_an_in_house_auditor", string="Is an in house auditor")

    pao_price_in_house_auditor = fields.Float(string="Price For In House Auditor", default=0.00,)

    
    