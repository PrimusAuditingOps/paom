from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SendAnniversaryReminder(models.TransientModel):
    _name = 'apply.exchange.rate.move.lines.wizard'
    _description = 'Apply exchange rate move lines wizard'
    
    move_id = fields.Many2one('account.move', string="Move", required=True)
    
    exchange_rate_lines_value = fields.Float(string="Exchange Rate", required=True, copy=False)
    
    currency_id = fields.Many2one('res.currency', string="Currency", default=None)
    
    @api.onchange('move_id')
    def _onchange_move_id(self):
        if not self.move_id:
            return

        currencies = self.move_id.invoice_line_ids.mapped(
            'product_id.base_currency_id'
        ).filtered(lambda c: c)

        return {
            'domain': {
                'currency_id': [('id', 'in', currencies.ids)]
            }
        }
    
    def apply_exchange_rate_lines_action(self):
        self.ensure_one()

        if self.move_id.state != 'draft' or not self.exchange_rate_lines_value:
            return

        lines_to_update = self.move_id.invoice_line_ids.filtered(
            lambda l: not l.exchange_rate_applied
        )

        if self.currency_id:
            lines_to_update = lines_to_update.filtered(
                lambda l: l.product_id.base_currency_id == self.currency_id
            )

        # if not lines_to_update:
        #     raise UserError(_("No lines found matching the selected currency."))

        for line in lines_to_update:
            line.price_unit *= self.exchange_rate_lines_value
            line.exchange_rate_value = self.exchange_rate_lines_value
            line.exchange_rate_applied = True

        return {'type': 'ir.actions.act_window_close'}
    
    
    def undo_exchange_rate_lines_action(self):
        self.ensure_one()

        if self.move_id.state != 'draft':
            return

        lines_to_update = self.move_id.invoice_line_ids.filtered(
            lambda l: l.exchange_rate_applied
        )

        if self.currency_id:
            lines_to_update = lines_to_update.filtered(
                lambda l: l.product_id.base_currency_id == self.currency_id
            )

        # if not lines_to_update:
        #     raise UserError(_("No lines found matching the selected currency."))

        for line in lines_to_update:
            line.price_unit /= line.exchange_rate_value
            line.exchange_rate_applied = False
            line.exchange_rate_value = None

        return {'type': 'ir.actions.act_window_close'}