from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _reverse_moves(self, default_values_list=None, cancel=False):
        reversed_moves = super()._reverse_moves(default_values_list=default_values_list, cancel=cancel)

        for original_move, reversed_move in zip(self, reversed_moves):
            original_lines = original_move.line_ids.sorted(lambda l: l.id)
            reversed_lines = reversed_move.line_ids.sorted(lambda l: l.id)

            for orig_line, rev_line in zip(original_lines, reversed_lines):
                rev_line.reversed_line_id = orig_line.id

        return reversed_moves

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    reversed_line_id = fields.Many2one(
        'account.move.line',
        string='Reversed Line',
        domain="[('move_id', '=', parent.reversed_entry_id)]",
        help='Reference to the original invoice line that this line reverses'
    )