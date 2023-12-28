from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapProductionSiteProduct(models.Model):
    _name = "pao.globalgap.production.site.product"
    _description = "GlobalGAP production site product"

    product_id = fields.Many2one(
        string="Product",
        comodel_name='servicereferralagreement.auditproducts',
        ondelete='restrict',
    )
    hectares_in_production = fields.Float(
        string="Hectares in production",
        digits=(16, 2),
    )
    to_certificate = fields.Selection(
        selection=[
            ('yes', "Yes"),
            ('no', "No"),
        ],
        string="To certificate", 
        copy=False,
        default='yes',
    )
    parallel_production_or_property = fields.Selection(
        selection=[
            ('yes', "Yes"),
            ('no', "No"),
        ],
        string="Parallel production/Parallel property", 
        copy=False,
        default='yes',
    )
    production_site_id = fields.Many2one(
        comodel_name='pao.globalgap.production.site',
        string='Production site',
        ondelete='restrict',
    )