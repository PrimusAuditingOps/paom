from odoo import fields, models
from logging import getLogger

_logger = getLogger(__name__)
class Partner(models.Model):
    _inherit='res.partner'

    
    """organization_id = fields.One2many(
        comodel_name='servicereferralagreement.organization',
        inverse_name='customer_id',
        string='Organizations',
    )"""
    organization_ids = fields.Many2many(
        'servicereferralagreement.organization',
        'servicereferralagreement_organization_res_partner_rel',
        'res_partner_id', 'servicereferralagreement_organization_id',
        string='Organizations',
    )

    vendor_service_percentage = fields.Float(
        default = 0.00,
        required = True,
        string= "Vendor service percentage",
    )
    
            
    
    
