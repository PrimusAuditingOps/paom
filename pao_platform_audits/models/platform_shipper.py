from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoPlatformShipper(models.Model):
    _name = "pao.platform.shipper"
    _description = "PAO Platform Shipper"

    name = fields.Char(
        required=True,
        string= "name",
    )
 