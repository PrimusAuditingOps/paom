from datetime import datetime, timedelta
from odoo import fields, models, api, _


 
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    pao_hub_brc_type = fields.Selection(
        selection=[
            ('brc', "BRC"),
            ('hub', "HUB"),
        ],
        string="BRC or HUB audit",
        copy=False, 
    )