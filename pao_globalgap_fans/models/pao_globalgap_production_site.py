from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapProductionSite(models.Model):
    _name = "pao.globalgap.production.site"
    _description = "GlobalGAP production site"

    
    name = fields.Char(
        string='Name', 
        copy=False,
    )
    type = fields.Selection(
        selection=[
            ('1', "Site"),
            ('2', "PHU"),
        ],
        string="Type", 
        copy=False,
        default='site',
    )
    address = fields.Text(
        string='Address', 
        copy=False,
    )
    city_id = fields.Many2one(
        string="City",
        comodel_name='res.city',
        ondelete='restrict',
    )
    state_city = fields.Char(
        string='State', 
        copy=False,
    )
    country_id = fields.Many2one(
        comodel_name = 'res.country', 
        string='Country', 
        ondelete='restrict',
    )  
    zip = fields.Char(
        string='ZIP', 
        copy=False,
    )
    telephone = fields.Char(
        string='Telephone', 
        copy=False,
    )
   
    email = fields.Char(
        string='Email', 
        copy=False,
    )
    latitude = fields.Float(
        string='Geo Latitude', 
        digits=(10, 7)
    )
    longitude = fields.Float(
        string='Geo Longitude', 
        digits=(10, 7)
    )
    contact_name = fields.Char(
        string='Contact name', 
        copy=False,
    )   
    contact_telephone = fields.Char(
        string='Contact telephone', 
        copy=False,
    )
    contact_email = fields.Char(
        string='Contact email', 
        copy=False,
    )
    contact_address = fields.Text(
        string='Contact address', 
        copy=False,
    )
    contact_zip = fields.Char(
        string='ZIP', 
        copy=False,
    )
    contact_city_id = fields.Many2one(
        string="City",
        comodel_name='res.city',
        ondelete='restrict',
    )
    contact_state_city = fields.Char(
        string='State', 
        copy=False,
    )
    contact_country_id = fields.Many2one(
        comodel_name = 'res.country', 
        string='Country', 
        ondelete='restrict',
    )  

    organization_id = fields.Many2one(
        comodel_name='pao.globalgap.organization',
        string='Organization',
        ondelete='restrict',
    )
    product_ids = fields.One2many(
        comodel_name='pao.globalgap.production.site.product',
        inverse_name='production_site_id',
        string='Products',
    )