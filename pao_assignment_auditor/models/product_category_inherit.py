from odoo import fields, models, api
from logging import getLogger

_logger = getLogger(__name__)
class ProductCategoryInherit(models.Model):

    _inherit='product.category'
    
    paa_schem_id = fields.Many2one(
        comodel_name='paa.assignment.auditor.scheme',
        string='Scheme',
        ondelete='set null',
    )
    paa_is_an_audit = fields.Boolean(
        string='Is a category of audits', 
        default=False,
    )