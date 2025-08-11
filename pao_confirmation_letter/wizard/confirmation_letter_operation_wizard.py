from odoo import api, fields, models, _
from logging import getLogger

_logger = getLogger(__name__)

class ConfirmationLetterOperationWizard(models.TransientModel):
    _name = 'pao.confirmation.letter.operation.wizard'
    _description = 'PAO Confirmation Letter Operation Wizard'


    wizard_id = fields.Many2one('pao.send.confirmation.letter.wizard', string='wizard_id')
    
    name = fields.Char(
        string="Operation Name",
        required=True,
    )
    operation_type = fields.Char(
        string="Operation Type",
        required=True,
    )

