from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapProductionSiteProductInformation(models.Model):
    _name = "pao.globalgap.production.site.product.information"
    _description = "GlobalGAP production site product information"

    product_id = fields.Many2one(
        string="Product",
        comodel_name='servicereferralagreement.auditproducts',
        ondelete='restrict',
    )
    uncovered_production_area = fields.Float(
        string="Uncovered production area",
        digits=(16, 2),
    )
    covered_production_area = fields.Float(
        string="Covered production area",
        digits=(16, 2),
    )
    applicable_harvest = fields.Selection(
        selection=[
            ('1', "Yes"),
            ('2', "No"),
        ],
        string="Applicable harvest", 
        copy=False,
        default='1',
    )
    harvest_type = fields.Selection(
        selection=[
            ('1', "First harvest"),
            ('2', "Later harvest"),
        ],
        string="Harvest type", 
        copy=False,
        default='1',
    )
    product_handling = fields.Selection(
        selection=[
            ('1', "No"),
            ('2', "Yes, in the field"),
            ('3', "Yes, in the PHU"),
        ],
        string="Product handling", 
        copy=False,
        default='1',
    )
    outsourced_activities = fields.Char(
        string='Outsourced activities', 
        copy=False,
    )
    ggn_gln_outsourced = fields.Char(
        string='GGN or GLN outsourced', 
        copy=False,
    )
    product_manipulated_not_certificate = fields.Selection(
        selection=[
            ('1', "No"),
            ('2', "Yes"),
        ],
        string="Product manipulated with product without certificate", 
        copy=False,
        default='1',
    )
    organization_buys_product = fields.Selection(
        selection=[
            ('1', "No"),
            ('2', "Yes"),
        ],
        string="The organization buy the same certified product and/or not certified?", 
        copy=False,
        default='1',
    )
    estimated_yield_in_tons = fields.Float(
        string="Estimated yield in tons",
        digits=(16, 2),
    )
    dates_harvest_estimated = fields.Char(
        string='Dates harvest estimated', 
        copy=False,
    )
    countries_of_products = fields.Many2many(
        'res.country',
        'country_production_site_product_information_rel',
        'production_site_product_information_id', 'country_id',
        string='Countries of products',
    )
    organization_id = fields.Many2one(
        comodel_name='pao.globalgap.organization',
        string='GLOBALG.A.P Organization',
        ondelete='restrict',
    )

