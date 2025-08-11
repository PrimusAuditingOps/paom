from odoo import fields, models

class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"
    _order = "pao_sequence, id asc"

    pao_sequence = fields.Integer(
        string='Sequence', 
        default=10
    )