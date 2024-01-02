from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class ResPartner(models.Model):

    _inherit='res.partner'
    

    pao_sc_price_list = fields.Many2one(
        string="Shared cost price list",
        comodel_name='product.pricelist',
        ondelete='set null',
        index=True,
    )