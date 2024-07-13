from odoo import fields, models, api
from random import randint



class PaoServicereFerralAgreementAuditproducts(models.Model):
    _name = 'servicereferralagreement.auditproducts'
    _description = 'Modelo para manejar el catalogo de productos auditados'
    _sql_constraints = [
        ('uc_name_version',
         'UNIQUE(name)',
         "There is already a product with this name"),
    ]

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Audit product', help='Enter Audit product',
                       required= True, translate=True)
    color =fields.Integer(string='Color Index', default=_get_default_color)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)