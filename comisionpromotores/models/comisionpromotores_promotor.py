from odoo import fields, models

class ComisionpromotoresPromotor(models.Model):
    
    _name = 'comisionpromotores.promotor'
    _description = 'Modelo para los promotores que llevan una comision'

    _sql_constraints = [
        ('percentage_check_zero',
         'CHECK(porcentaje >= 0)',
         "the percentage must be greater than or equal to 0"),
         ('percentage_check_onehundred',
         'CHECK(porcentaje < 101)',
         "the percentage must be less than or equal to 100"),
    ]

    name = fields.Char(
        required=True,
        string= "Promoter",
    )
    porcentaje = fields.Integer(
        default = 0,
        required = True,
        string= "Commission percentage",
    )
    cliente_id = fields.One2many(
        comodel_name='res.partner',
        inverse_name='promotor_id',
        string='Customer',
    )
    