from odoo import fields, models

class PaoConfirmationLetterOperations(models.Model):

    _name = 'pao.confirmation.letter.operations'
    _description = 'PAO Confirmation Letter Operations'

    name = fields.Char(
        string="Operation Name",
        required=True,
    )
    operation_type = fields.Char(
        string="Operation Type",
        required=True,
    )
