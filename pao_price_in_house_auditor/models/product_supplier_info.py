from odoo import fields, models, api

class ProductSupplierInfor(models.Model):
    _inherit='product.supplierinfo'

    def _get_in_house_auditor(self):
        return self.partner_id.is_an_in_house_auditor 

    pao_price_in_house_auditor = fields.Float(string="Price For In House Auditor", readonly=_get_in_house_auditor, default=0.00,)

    
    