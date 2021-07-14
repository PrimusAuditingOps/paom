from odoo import fields, models, api
class ServicereferralagreementEntity(models.Model):
    _name = 'servicereferralagreement.entity'
    _description = 'Modelo para manejar el catalogo de entidades/operaciones'

    name = fields.Char(
        string="Entity",
        help='Enter Name',
        required= True,
    )
    country_id = fields.Many2one(
        comodel_name = 'res.country', 
        string='Country', 
        help='Select Country', 
        ondelete='restrict',
        required=True,
    )  
    state_id = fields.Many2one(
        comodel_name = "res.country.state", 
        string='State', 
        help='Select State', 
        ondelete='restrict',
        required=True,

    )
    city = fields.Char(
        string='City', 
        help='Enter City',
        required=True, 
    )  
    address = fields.Text(
        string='Address',
        help='Enter Address'
    )
    organization_id = fields.Many2one(
        comodel_name='servicereferralagreement.organization',
        string='Organization',
        ondelete='set null',
    )
    

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            return {'domain': {'state_id': [('country_id', '=', self.country_id.id)]}}
        else:
            return {'domain': {'state_id': []}}