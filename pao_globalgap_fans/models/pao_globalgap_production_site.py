from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapProductionSite(models.Model):
    _name = "pao.globalgap.production.site"
    _description = "GLOBALG.A.P. production site"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Name', 
        copy=False,
        tracking=True,
    )
    type = fields.Selection(
        selection=[
            ('1', "Site"),
            ('2', "PHU"),
        ],
        string="Type", 
        copy=False,
        default='site',
        tracking=True,
    )
    address = fields.Text(
        string='Address', 
        copy=False,
        tracking=True,
    )
    postal_address = fields.Text(
        string='Postal address', 
        copy=False,
        tracking=True,
    )
    city_id = fields.Many2one(
        string="City",
        comodel_name='res.city',
        ondelete='restrict',
        tracking=True,
    )
    state_id = fields.Many2one(
        comodel_name = 'res.country.state', 
        string='State', 
        ondelete='restrict',
        tracking=True,
    ) 
    country_id = fields.Many2one(
        comodel_name = 'res.country', 
        string='Country', 
        ondelete='restrict',
        tracking=True,
    )  
    zip = fields.Char(
        string='ZIP', 
        copy=False,
        tracking=True,
    )
    telephone = fields.Char(
        string='Telephone', 
        copy=False,
        tracking=True,
    )
   
    email = fields.Char(
        string='Email', 
        copy=False,
        tracking=True,
    )
    latitude = fields.Float(
        string='Geo Latitude', 
        digits=(10, 7),
        tracking=True,
    )
    longitude = fields.Float(
        string='Geo Longitude', 
        digits=(10, 7),
        tracking=True,
    )
    contact_name = fields.Char(
        string='Contact name', 
        copy=False,
        tracking=True,
    )   
    contact_telephone = fields.Char(
        string='Contact telephone', 
        copy=False,
        tracking=True,
    )
    contact_email = fields.Char(
        string='Contact email', 
        copy=False,
        tracking=True,
    )
    contact_address = fields.Text(
        string='Contact address', 
        copy=False,
        tracking=True,
    )
    contact_zip = fields.Char(
        string='Contact ZIP', 
        copy=False,
        tracking=True,
    )
    contact_city_id = fields.Many2one(
        string="Contact City",
        comodel_name='res.city',
        ondelete='restrict',
        tracking=True,
    )
    contact_state_id = fields.Many2one(
        comodel_name = 'res.country.state', 
        string='Contact State', 
        ondelete='restrict',
        tracking=True,
    ) 
    contact_country_id = fields.Many2one(
        comodel_name = 'res.country', 
        string='Contact Country', 
        ondelete='restrict',
    )  

    organization_id = fields.Many2one(
        comodel_name='pao.globalgap.organization',
        string='Organization',
        ondelete='restrict',
        tracking=True,
    )
    product_ids = fields.One2many(
        comodel_name='pao.globalgap.production.site.product',
        inverse_name='production_site_id',
        string='Products',
        tracking=True,
    )