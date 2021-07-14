from odoo import fields, models, api
from random import randint
class ServicereferralagreementAuditproducts(models.Model):
    _name = 'servicereferralagreement.auditproducts'
    _description = 'Modelo para manejar el catalogo de productos auditados'
    _sql_constraints = [
        ('uc_name_version',
         'UNIQUE(name)',
         "There is already a product with this name"),
    ]
    def _get_default_color(self):
        return randint(1, 11)
    name = fields.Char(
        string="Audit product",
        help='Enter Audit product',
        required= True,
        translate=True,
    )
    color =fields.Integer(
        string='Color Index', 
        default=_get_default_color
    )