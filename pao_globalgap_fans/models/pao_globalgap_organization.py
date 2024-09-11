from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapOrganization(models.Model):
    _name = "pao.globalgap.organization"
    _description = "GLOBALG.A.P. Organization"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(
        string='Name', 
        tracking=True,
    )
    unannounced = fields.Boolean(
        string="Unannounced",
        default=False,
    )
    plmx = fields.Char(
        string='PL-México', 
        tracking=True,
    )
    website = fields.Char(
        string='Website', 
        tracking=True,
        default="The organization does not have a website.",
    )
    ggn = fields.Char(
        string='GGN', 
        tracking=True,

    )
    globalgap_version = fields.Selection(
        selection=[
            ('1', "V5.4-1-GFS"),
            ('2', "V5.3-GFS"),
        ],
        string="GLOBALG.A.P version", 
        default='1',
        tracking=True,
    )
    certification_option = fields.Selection(
        selection=[
            ('1', "Opción 1. Productor Individual"),
            ('2', "Opción 1. Productor Multisitio sinSGC"),
        ],
        string="Certification option", 
        default='1',
        tracking=True,
    )

    addons_ids = fields.Many2many(
        'pao.globalgap.addon',
        'globalgap_addon_organization_rel',
        'globalgap_organization_id', 'globalgap_addon_id',
        string='Addons',
        tracking=True,
    )

    evaluation_type = fields.Selection(
        selection=[
            ('1', "Certificación Inicial"),
            ('2', "Re-certificación"),
            ('3', "Ampliación de Alcance"),
            ('4', "Reducción de Alcance"),
        ],
        string="Evaluation type", 
        default='1',
        tracking=True,
    )
    address = fields.Text(
        string='Address', 
        tracking=True,
    )
    colony = fields.Char(
        string='Colony', 
        tracking=True,
        default="",
    )
    postal_address = fields.Text(
        string='Postal address', 
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
        tracking=True,
    )
    telephone = fields.Char(
        string='Telephone', 
        tracking=True,
    )
    email = fields.Char(
        string='Email', 
        tracking=True,
    )
    gln = fields.Char(
        string='GLN', 
        tracking=True,
    )
    vat = fields.Char(
        string='VAT', 
        tracking=True,
    )
    previous_cb = fields.Char(
        string='Previous CB', 
        tracking=True,
    )
    previous_ggn = fields.Char(
        string='Previous GGN', 
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
        tracking=True,
    )   
    contact_telephone = fields.Char(
        string='Contact telephone', 
        tracking=True,
    )
    contact_fax = fields.Char(
        string='Contact fax', 
        tracking=True,
    )
    contact_email = fields.Char(
        string='Contact email', 
        tracking=True,
    )
    contact_position = fields.Char(
        string='Contact position', 
        tracking=True,
    )
    rights_of_access = fields.Selection(
        selection=[
            ('1', "Si, el productor se compromete a permitir el acceso a la dirección de su empresa por parte del grupo público de acceso."),
            ('2', "No, el productor no permite el acceso a la dirección de su empresa para el grupo público de acceso."),
        ],
        string="Address access permissions", 
        default='1',
        tracking=True,
    )
    number_of_hired_workers = fields.Integer(
        string='Number of hired workers', 
        default=0,
        tracking=True,
    )
    number_of_subcontracted_workers = fields.Integer(
        string='Number of subcontracted workers', 
        default=0,
        tracking=True,
    )
    production_site_ids = fields.One2many(
        comodel_name='pao.globalgap.production.site',
        inverse_name='organization_id',
        string='Production sites',
        tracking=True,
        copy=False,
    )
    """
    fan_request_ids = fields.One2many(
        comodel_name='pao.globalgap.fans.request',
        inverse_name='organization_id',
        string='GLOBALG.A.P. Fans request',
    )"""
    product_information_ids = fields.One2many(
        comodel_name='pao.globalgap.production.site.product.information',
        inverse_name='organization_id',
        string='Production site product information',
        tracking=True,
        copy=False,
    )
    version_id = fields.Many2one(
        comodel_name='pao.globalgap.version',
        string='Version',
        ondelete='restrict',
        tracking=True,
    )
    certification_option_id = fields.Many2one(
        comodel_name='pao.globalgap.certification.option',
        string='Certification Option',
        ondelete='restrict',
        tracking=True,
    )