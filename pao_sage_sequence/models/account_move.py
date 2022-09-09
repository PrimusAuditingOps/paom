from odoo import api, exceptions, fields, models, _
from logging import getLogger

_logger = getLogger(__name__)

class AccountMove(models.Model):
    _inherit='account.move'
    
    pao_sage_folio = fields.Char(
        string = 'folio SAGE',
    )
