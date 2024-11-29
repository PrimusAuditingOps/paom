from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class SaleOrder(models.Model):
    _inherit='res.partner'

    blockout_dates_ids = fields.One2many('pao.audit.blockout.dates', string="Blockout Dates", inverse_name="partner_id")