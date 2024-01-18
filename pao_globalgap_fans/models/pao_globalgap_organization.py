from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapOrganization(models.Model):
    _name = "pao.globalgap.organization"
    _description = "GLOBALG.A.P. Organization"



    name = fields.Char(
        string='Name', 
        copy=False,
    )
    plmx = fields.Char(
        string='PL-México', 
        copy=False,

    )
    ggn = fields.Char(
        string='GGN', 
        copy=False,

    )
    globalgap_version = fields.Selection(
        selection=[
            ('1', "V5.4-1-GFS"),
            ('2', "V5.3-GFS"),
        ],
        string="GLOBALG.A.P version", 
        copy=False,
        default='1',
    )
    certification_option = fields.Selection(
        selection=[
            ('1', "Opción 1. Productor Individual"),
            ('2', "Opción 1. Productor Multisitio sinSGC"),
        ],
        string="Certification option", 
        copy=False,
        default='1',
    )

    addons_ids = fields.Many2many(
        'pao.globalgap.addon',
        'globalgap_addon_organization_rel',
        'globalgap_organization_id', 'globalgap_addon_id',
        string='Addons',
    )

    evaluation_type = fields.Selection(
        selection=[
            ('1', "Certificación Inicial"),
            ('2', "Re-certificación"),
            ('3', "Ampliación de Alcance"),
            ('4', "Reducción de Alcance"),
        ],
        string="Evaluation type", 
        copy=False,
        default='1',
    )
    address = fields.Text(
        string='Address', 
        copy=False,
    )
    postal_address = fields.Text(
        string='Postal address', 
        copy=False,
    )
    city_id = fields.Many2one(
        string="City",
        comodel_name='res.city',
        ondelete='restrict',
    )
    state_id = fields.Many2one(
        comodel_name = 'res.country.state', 
        string='State', 
        ondelete='restrict',
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
    gln = fields.Char(
        string='GLN', 
        copy=False,
    )
    vat = fields.Char(
        string='VAT', 
        copy=False,
    )
    previous_cb = fields.Char(
        string='Previous CB', 
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
    contact_fax = fields.Char(
        string='Contact fax', 
        copy=False,
    )
    contact_email = fields.Char(
        string='Contact email', 
        copy=False,
    )
    contact_position = fields.Char(
        string='Contact position', 
        copy=False,
    )
    rights_of_access = fields.Selection(
        selection=[
            ('1', "Si, el productor se compromete a permitir el acceso a la dirección de su empresa por parte del grupo público de acceso."),
            ('2', "No, el productor no permite el acceso a la dirección de su empresa para el grupo público de acceso."),
        ],
        string="Address access permissions", 
        copy=False,
        default='1',
    )
    number_of_hired_workers = fields.Integer(
        string='Number of hired workers', 
        default=0,
    )
    number_of_subcontracted_workers = fields.Integer(
        string='Number of subcontracted workers', 
        default=0,
    )
    production_site_ids = fields.One2many(
        comodel_name='pao.globalgap.production.site',
        inverse_name='organization_id',
        string='Production sites',
    )
    fan_request_ids = fields.One2many(
        comodel_name='pao.globalgap.fans.request',
        inverse_name='organization_id',
        string='GLOBALG.A.P. Fans request',
    )
    product_information_ids = fields.One2many(
        comodel_name='pao.globalgap.production.site.product.information',
        inverse_name='organization_id',
        string='Production site product information',
    )
    version_id = fields.Many2one(
        comodel_name='pao.globalgap.version',
        string='Version',
        ondelete='restrict',
    )
    certification_option_id = fields.Many2one(
        comodel_name='pao.globalgap.certification.option',
        string='Certification Option',
        ondelete='restrict',
    )