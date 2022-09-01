from odoo import fields, models, api
from logging import getLogger

_logger = getLogger(__name__)
class ProductTemplateInherit(models.Model):

    _inherit='product.template'
    
    paa_is_an_audit = fields.Boolean(
        string='Is an audit', 
        default=False,
    )
    paa_schem_id = fields.Many2one(
        comodel_name='paa.assignment.auditor.scheme',
        string='Scheme',
        ondelete='set null',
    )