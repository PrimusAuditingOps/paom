from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SendAnniversaryReminder(models.TransientModel):
    _name = 'apply.exchange.rate.move.lines.wizard'
    _description = 'Apply exchange rate move lines wizard'
    
    move_id = fields.Many2one('account.move', string="Move", required=True)
    
    exchange_rate_lines_value = fields.Float(string="Exchange Rate", required=True, copy=False)
    
    currency_id = fields.Many2one(
        'res.currency',
        domain="[('id', 'in', available_currency_ids)]"
    )
    
    available_currency_ids = fields.Many2many(
        'res.currency',
        compute='_compute_available_currencies'
    )

    @api.depends('move_id')
    def _compute_available_currencies(self):
        for wizard in self:
            if wizard.move_id:
                currencies = wizard.move_id.invoice_line_ids.mapped(
                    'product_id.base_currency_id'
                ).filtered(lambda c: c)
                wizard.available_currency_ids = currencies
            else:
                wizard.available_currency_ids = False
    
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