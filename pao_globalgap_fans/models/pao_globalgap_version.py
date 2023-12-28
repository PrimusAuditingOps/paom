from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapVersion(models.Model):
    _name = "pao.globalgap.version"
    _description = "GlobalGAP Version"

    name = fields.Char(
        string='Name', 
        copy=False,
        translate=True, 
    )
   