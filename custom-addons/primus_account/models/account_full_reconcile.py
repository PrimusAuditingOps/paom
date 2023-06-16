from odoo import api, fields, models


class AccountFullReconcile(models.Model):
    _inherit = "account.full.reconcile"

    @api.model
    def create(self, vals):
        account_move_line_obj = self.env["account.move.line"]
        res = super(AccountFullReconcile, self).create(vals)
        res.flush()
        for reconcile in res:
            lines_ids = reconcile.reconciled_line_ids.mapped('move_id.line_ids')._reconciled_lines()
            move_lines = account_move_line_obj.browse(lines_ids)
            for line in move_lines:
                if line.move_id.payment_id:
                    line.payment_id.reconciliation_date = line.payment_id.date
                    move_lines.mapped('move_id').write({'reconciliation_date': line.payment_id.date})
                    reconcile.write({'reconciliation_date': line.payment_id.date})
        return res
