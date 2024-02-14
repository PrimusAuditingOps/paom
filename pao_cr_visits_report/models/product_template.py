from datetime import datetime, timedelta
from odoo import fields, models, api
from logging import getLogger

_logger = getLogger(__name__)
class ProductTemplate(models.Model):

    _inherit='product.template'
    
    pao_cr_vr_services_id = fields.Many2one(
        string="CR visits reports service",
        comodel_name='pao.cr.visits.report.services',
        ondelete='set null',
        index=True,
    )
    