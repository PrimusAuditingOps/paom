from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class ProductProduct(models.Model):

    _inherit='product.product'
    

    pao_audit_template_id = fields.Many2one(
        comodel_name='pao.azz.audit.template',
        string='Audit Template',
        ondelete='restrict',
    )    