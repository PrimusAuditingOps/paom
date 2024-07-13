from odoo import fields, models, api



class PaoServicereFerralAgreementOrganization(models.Model):
    _name = 'servicereferralagreement.organization'
    _description = 'Modelo para manejar el catalogo de organizaciones/productores'

    _sql_constraints = [
        ('uc_name_organization',
         'UNIQUE(name)',
         "There is already a organization with this name"),
    ]

    @api.model
    def _default_country(self):
        return self.env['res.country'].search(
            ['|',('name','=','Mexico'),('name','=','México')], limit=1)

    name = fields.Char(string="Organization", help='Enter Name', required= True)
    rfc = fields.Char(string="RFC", help='Enter RFC')
    country_id = fields.Many2one('res.country', string='Country', help='Select Country',
                                 ondelete='restrict', required=True,
                                 default = _default_country)  
    state_id = fields.Many2one('res.country.state', string='State', help='Select State',
                               ondelete='restrict', required=True,
                               domain=[('country_id', '=', -1)])
    city = fields.Char(string='City', help='Enter City', required=True)  
    address = fields.Text(string='Address', help='Enter Address')
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)
    registry_number_id = fields.One2many('servicereferralagreement.registrynumber',
                                         inverse_name='organization_id',
                                         string='Registry number')