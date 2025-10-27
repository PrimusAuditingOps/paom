from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoPlatformAuditor(models.Model):
    _name = "pao.platform.auditor"
    _description = "PAO Platform Auditor"

    name = fields.Char(
        required=True,
        string= "name",
    )
    active = fields.Boolean(string="Active", default=True)
    