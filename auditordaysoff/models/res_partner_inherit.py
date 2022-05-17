from odoo import fields, models, api
from logging import getLogger

_logger = getLogger(__name__)
class PartnerInherit(models.Model):
    _inherit='res.partner'

    ado_is_auditor = fields.Boolean(
        string = "Is an auditor",
        default = False,
    )