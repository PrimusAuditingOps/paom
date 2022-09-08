from odoo import fields, models

class PaoShippers(models.Model):
    
    _name = 'pao.shippers'
    _description = 'Modelo para los shippers'

    name = fields.Char(
        required=True,
        string= "Shipper",
    )
    customer_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='pao_shipper_id',
        string='Customers',
    )
    