from odoo import fields, models, api
class PaoCrSchemes(models.Model):
    _name = 'pao.cr.schemes'
    _description = 'Customer relation Schemes'
    
    _sql_constraints = [
        ('uc_name_cr_schemes',
         'UNIQUE(name)',
         "There is already a Scheme with this name"),
    ]

    name = fields.Char(
        string="Scheme",
        help='Enter a Scheme',
        required= True,
    )

   