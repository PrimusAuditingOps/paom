from odoo import models, fields, api

class CurrencyChangeWizard(models.TransientModel):
    _name = 'auto.currency.conversion.wizard'
    _description = 'Auto Currency Conversion Wizard'

    move_id = fields.Many2one('account.move', string='Invoice')
    from_currency_id = fields.Many2one('res.currency', string='From Currency')
    to_currency_id = fields.Many2one('res.currency', string='To Currency')
    exchange_rate = fields.Float(string='Exchange Rate', digits=(12, 6), readonly=True)
    date = fields.Date(string='Date', readonly=True)

    # @api.model
    # def default_get(self, fields_list):
    #     res = super().default_get(fields_list)
    #     if self.env.context.get('default_move_id'):
    #         move = self.env['account.move'].browse(self.env.context['default_move_id'])
    #         from_currency = self.env.context.get('from_currency_id')
    #         to_currency = self.env.context.get('to_currency_id')
    #         date = move.invoice_date or fields.Date.today()

    #         if from_currency and to_currency:
    #             from_cur = self.env['res.currency'].browse(from_currency)
    #             to_cur = self.env['res.currency'].browse(to_currency)
    #             # Get exchange rate: how many MXN per 1 USD
    #             rate = from_cur._get_conversion_rate(from_cur, to_cur, move.company_id, date)
    #             res.update({
    #                 'move_id': move.id,
    #                 'from_currency_id': from_currency,
    #                 'to_currency_id': to_currency,
    #                 'exchange_rate': rate,
    #                 'date': date,
    #             })
    #     return res

    def apply_currency_change(self):
        self.ensure_one()
        move = self.move_id
        from_cur = self.from_currency_id
        to_cur = self.to_currency_id
        date = move.invoice_date or fields.Date.today()

        for line in move.invoice_line_ids:
            line.price_unit = from_cur._convert(
                line.price_unit,
                to_cur,
                move.company_id,
                date,
            )
            line.exchange_rate_applied = True

        return {'type': 'ir.actions.act_window_close'}

    # def reject_currency_change(self):
    #     self.ensure_one()
    #     # Revert currency back to original
    #     self.move_id.currency_id = self.from_currency_id
    #     return {'type': 'ir.actions.act_window_close'}