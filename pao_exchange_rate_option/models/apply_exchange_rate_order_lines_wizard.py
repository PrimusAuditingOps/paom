from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ApplyExchangeRateOrderLinesWizard(models.TransientModel):
    _name = 'apply.exchange.rate.purchase.order.lines.wizard'
    _description = 'Apply exchange rate purchase order lines wizard'
    
    order_id = fields.Many2one('purchase.order', string="Purchase Order", required=True)
    
    exchange_rate_lines_value = fields.Float(string="Exchange Rate", default=None, required=True, copy=False)
    
    currency_id = fields.Many2one('res.currency')
    
    undo_action = fields.Boolean()
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['undo_action'] = self.env.context.get('undo_action', False)
        return res
    
    can_edit_exchange_rate = fields.Boolean(
        compute='_compute_can_edit_exchange_rate'
    )

    @api.depends_context('uid')
    def _compute_can_edit_exchange_rate(self):
        for wizard in self:
            wizard.can_edit_exchange_rate = self.env.user.has_group(
                'account.group_account_manager'
            )
    
    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        if self.currency_id:
            exchange_rate = self.env['servicereferralagreement.auditorexchangerate'].sudo().search([
                ('currency_id', '=', self.currency_id.id),
            ], limit=1)

            self.exchange_rate_lines_value = (
                exchange_rate.exchange_rate if exchange_rate else None
            )

    def apply_exchange_rate_lines_action(self):
        self.ensure_one()

        if self.order_id.state != 'draft':
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
            
        lines_to_update = self.order_id.order_line.filtered(
                lambda l: not l.exchange_rate_applied
            )

        updated_lines_count = len(lines_to_update)
        
        if updated_lines_count <= 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('No lines were updated with the exchange rate.'),
                    'message': _('No lines were updated. Please ensure there are lines without an exchange rate applied.'),
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            for line in lines_to_update:
                line.price_unit *= self.exchange_rate_lines_value
                line.exchange_rate_value = self.exchange_rate_lines_value
                line.exchange_rate_applied = True
                
            self.order_id.previous_currency_id = self.order_id.currency_id
            self.order_id.currency_id = self.currency_id
            
            self.order_id.exchange_rate_applied_to_po = True
                
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

        if self.order_id.state != 'draft':
            return
        
        lines_to_update = self.order_id.order_line.filtered(
                lambda l: l.exchange_rate_applied
            )
            
        updated_lines_count = len(lines_to_update)

        if updated_lines_count <= 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('No lines were reverted.'),
                    'message': _('No lines were updated. Please ensure there are lines with an exchange rate applied.'),
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            for line in lines_to_update:
                line.price_unit /= line.exchange_rate_value
                line.exchange_rate_applied = False
                line.exchange_rate_value = None
                
            self.order_id.currency_id = self.order_id.previous_currency_id
            self.order_id.previous_currency_id = None
            
            self.order_id.exchange_rate_applied_to_po = False

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
        