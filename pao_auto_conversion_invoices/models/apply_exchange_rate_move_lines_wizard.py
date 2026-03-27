from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ApplyExchangeRateMoveLinesWizard(models.TransientModel):
    _name = 'apply.exchange.rate.move.lines.wizard'
    _description = 'Apply exchange rate move lines wizard'
    
    move_id = fields.Many2one('account.move', string="Move", required=True)
    
    exchange_rate_lines_value = fields.Float(string="Exchange Rate", default=None, required=True, copy=False)
    
    currency_id = fields.Many2one('res.currency', domain="[('id', 'in', available_currency_ids)]")
    
    available_currency_ids = fields.Many2many('res.currency', compute='_compute_available_lines_currencies')
    
    undo_action = fields.Boolean()
    
    manual_selection = fields.Boolean(string="Select lines manually", default=False)
    
    line_ids = fields.Many2many(
        'account.move.line',
        string="Invoice Lines",
        domain="[('id', 'in', available_line_ids)]"
    )
    
    available_line_ids = fields.Many2many(
        'account.move.line',
        compute="_compute_available_lines_currencies"
    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['undo_action'] = self.env.context.get('undo_action', False)
        return res

    @api.depends('move_id.invoice_line_ids', 'move_id.invoice_line_ids.exchange_rate_applied', 'undo_action')
    def _compute_available_lines_currencies(self):
        for wizard in self:
            if not wizard.move_id:
                wizard.available_currency_ids = False
                wizard.available_line_ids = False
                continue

            lines = wizard.move_id.invoice_line_ids

            if not wizard.undo_action:
                lines = lines.filtered(lambda l: not l.exchange_rate_applied)
            else:
                lines = lines.filtered(lambda l: l.exchange_rate_applied)
                
            wizard.available_line_ids = lines

            currencies = lines.mapped('product_id.base_currency_id').filtered(lambda c: c)

            wizard.available_currency_ids = currencies
    
    def apply_exchange_rate_lines_action(self):
        self.ensure_one()

        if self.move_id.state != 'draft':
            return
        
        if not self.exchange_rate_lines_value:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('Invalid Exchange Rate value.'),
                    'message': _('Please enter a valid exchange rate before applying.'),
                    'sticky': False,
                }
            }
            
        if self.manual_selection:
            lines_to_update = self.line_ids
        else:
            lines_to_update = self.move_id.invoice_line_ids.filtered(
                lambda l: not l.exchange_rate_applied
            )

            if self.currency_id:
                lines_to_update = lines_to_update.filtered(
                    lambda l: l.product_id.base_currency_id == self.currency_id
                )

        updated_lines_count = len(lines_to_update)
        
        if updated_lines_count <= 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('No lines were updated with the exchange rate.'),
                    'message': _('No lines were updated. Please verify the selected currency and ensure there are lines without an exchange rate applied.'),
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            for line in lines_to_update:
                line.price_unit *= self.exchange_rate_lines_value
                line.exchange_rate_value = self.exchange_rate_lines_value
                line.exchange_rate_applied = True
                
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'title': _('Exchange Rate Applied'),
                    'message': _('The exchange rate has been applied to %s line(s).') % updated_lines_count,
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        
    
    def undo_exchange_rate_lines_action(self):
        self.ensure_one()

        if self.move_id.state != 'draft':
            return

        if self.manual_selection:
            lines_to_update = self.line_ids
        else:
            lines_to_update = self.move_id.invoice_line_ids.filtered(
                lambda l: l.exchange_rate_applied
            )

            if self.currency_id:
                lines_to_update = lines_to_update.filtered(
                    lambda l: l.product_id.base_currency_id == self.currency_id
                )
            
        updated_lines_count = len(lines_to_update)

        if updated_lines_count <= 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('No lines were reverted.'),
                    'message': _('No lines were updated. Please verify the selected currency and ensure there are lines with an exchange rate applied.'),
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            for line in lines_to_update:
                line.price_unit /= line.exchange_rate_value
                line.exchange_rate_applied = False
                line.exchange_rate_value = None

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'title': _('Exchange Rate Reverted'),
                    'message': _('The exchange rate has been reverted to %s line(s).') % updated_lines_count,
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        