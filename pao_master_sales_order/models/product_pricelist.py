from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class ProductPricelist(models.Model):

    _inherit='product.pricelist'
    

    pao_is_a_shared_cost_list = fields.Boolean(
        string= "Is a Tier4 price list",
        default= False,
        copy= False,
    )