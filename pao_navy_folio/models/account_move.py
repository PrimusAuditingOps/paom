from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    pao_navy_folio = fields.Char(string="Folio Navy")
    