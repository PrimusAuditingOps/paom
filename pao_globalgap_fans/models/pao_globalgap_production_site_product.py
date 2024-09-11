from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapProductionSiteProduct(models.Model):
    _name = "pao.globalgap.production.site.product"
    _description = "GLOBALG.A.P. production site product"

    product_id = fields.Many2one(
        string="Product",
        comodel_name='servicereferralagreement.auditproducts',
        ondelete='restrict',
    )
    hectares_in_production = fields.Float(
        string="Hectares in production",
        digits=(16, 4),
    )
    to_certificate = fields.Selection(
        selection=[
            ('1', "Si"),
            ('2', "No"),
        ],
        string="To certificate", 
        copy=False,
        default='1',
    )
    parallel_production = fields.Selection(
        selection=[
            ('1', "No"),
            ('2', "Si"),
        ],
        string="Parallel production", 
        copy=False,
        default='1',
    )
    parallel_property = fields.Selection(
        selection=[
            ('1', "No"),
            ('2', "Si"),
        ],
        string="Parallel property", 
        copy=False,
        default='1',
    )
    production_site_id = fields.Many2one(
        comodel_name='pao.globalgap.production.site',
        string='Production site',
        ondelete='cascade',
    )