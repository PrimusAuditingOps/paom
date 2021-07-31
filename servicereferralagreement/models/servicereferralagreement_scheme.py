from odoo import fields, models, api
class ServicereferralagreementScheme(models.Model):
    _name = 'servicereferralagreement.scheme'
    _description = 'Modelo para manejar el catalogo de esquemas'
    _sql_constraints = [
        ('uc_name_version',
         'UNIQUE(name,version)',
         "There is already a schema with this version"),
    ]

    def _get_name(self):
        for record in self:
            record.display_name_scheme = '{0} {1}'.format(record.name, record.version) 

    name = fields.Char(
        string="Scheme",
        help='Enter scheme',
        required= True,
    )
    version = fields.Char(
        string="Version",
        help="Enter Version",
    )