from odoo import fields, models



class PaoShippers(models.Model):
    _name='pao.shippers'
    _description='Modelo para los shippers'

    name = fields.Char(required=True, string="Shipper")
    customer_ids = fields.One2many('res.partner', inverse_name='pao_shipper_id',
                                   string='Customers')
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company) 