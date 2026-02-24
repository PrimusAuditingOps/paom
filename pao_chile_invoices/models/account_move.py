from odoo import models, fields, _

class AccountMoveInherit(models.Model):

    _inherit='account.move'
    
    auto_exchange_rate_lines_value = fields.Float(string="Exchange Rate", copy=False)
    
    exchange_rate_applied = fields.Boolean(default=False, copy=False)
    
    def apply_exchange_rate_lines_action(self):
        for move in self:
            rate = move.auto_exchange_rate_lines_value

            if move.state != 'draft' or not rate or move.exchange_rate_applied:
                continue

            for line in move.invoice_line_ids:
                if line.price_unit:
                    new_price = line.price_unit * rate
                    line.price_unit = new_price
                    
            move.exchange_rate_applied = True
    
    def undo_exchange_rate_lines_action(self):
        for move in self:
            rate = move.auto_exchange_rate_lines_value

            if move.state != 'draft' or not rate or not move.exchange_rate_applied:
                continue 

            for line in move.invoice_line_ids:
                if line.price_unit:
                    new_price = line.price_unit / rate
                    line.price_unit = new_price
                    
            move.exchange_rate_applied = False
            
    def remove_fees_lines_action(self):
        for move in self:
            fee_lines = move.invoice_line_ids.filtered(
                lambda line: line.name and line.name.startswith('FEE ')
            )
            if fee_lines:
                fee_lines.unlink()
            
