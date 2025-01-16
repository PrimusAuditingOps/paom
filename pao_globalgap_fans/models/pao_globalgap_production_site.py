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
    
    site_is = fields.Selection(
        selection=[
            ('own', "Own"),
            ('leased_no_contract', "Leased (Without Contract)"),
            ('leased_contract', "Leased (With Contract)"),
        ],
        string="Site Is", 
        copy=False,
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
    
    not_direct_line_memebers_grasp = fields.Selection(
        selection=[
            ('2', "No"),
            ('1', "Si"),
        ],
        string="Do you employ workers who are not part of the immediate family? (direct line only)", 
        copy=False,
        default=None,
    )
    
    not_direct_line_quantity_members_grasp = fields.Char(string="Staff Count")
    
    not_direct_line_relation_members = fields.Char(string="Relation")
    
    grasp_staff_ids = fields.One2many(
        comodel_name='pao.grasp.staff.details',
        inverse_name='production_site_id',
        string='GRASP Staff Details',
        tracking=True,
        readonly=True
    )
    
    total_members = fields.Char(string="Total Members")
    members_with_workers = fields.Char(string="Members with workers")
    members_without_workers = fields.Char(string="Members without workers")
     
    any_grasp_addon = fields.Boolean(
        string='Has GRASP Addon',
        compute='_compute_any_grasp_addon',
        store=True,
    )
    
    any_grasp_addon = fields.Boolean(
        string='Has GRASP Addon',
        compute='_compute_any_grasp_addon',
        store=True,
    )
    
    fill_extra_data_grasp_module = fields.Boolean(
        compute='_compute_fill_extra_data_grasp_module',
        store=True,
    )

    @api.depends('organization_id.addons_ids')
    def _compute_any_grasp_addon(self):
        for record in self:
            if record.organization_id:
                grasp_addons = record.organization_id.addons_ids.filtered(lambda addon: addon.is_grasp_module)
                record.any_grasp_addon = bool(grasp_addons)
            else:
                record.any_grasp_addon = False
                
    @api.depends('organization_id.certification_option_id')
    def _compute_fill_extra_data_grasp_module(self):
        for record in self:
            if record.organization_id and record.any_grasp_addon and record.organization_id.certification_option_id.id in (3, 4):
                record.fill_extra_data_grasp_module = True
            else:
                record.fill_extra_data_grasp_module = False
