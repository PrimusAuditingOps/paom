from odoo import fields, models, api
from logging import getLogger

_logger = getLogger(__name__)
class ProductTemplate(models.Model):

    _inherit='product.template'
    
    can_be_commissionable = fields.Boolean(
        string='Can be Commissionable', 
        default=False,
    )