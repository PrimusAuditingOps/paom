from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class SaleOrder(models.Model):
    _inherit='sale.order'

    
    pao_promotor_id = fields.Many2one(
        comodel_name='comisionpromotores.promotor',
        string='Consultant',
        ondelete='set null',
    )