from odoo import models, fields, api, _

class PurchaseOrderInherit(models.Model):

    _inherit='purchase.order'

    can_apply_exchange_rate = fields.Boolean(
        compute='_compute_exchange_rate_buttons'
    )
    can_undo_exchange_rate = fields.Boolean(
        compute='_compute_exchange_rate_buttons'
    )
    
    previous_currency_id = fields.Many2one('res.currency', copy=False, default=None)
    
    exchange_rate_applied_to_po = fields.Boolean(default=False, copy=False)

    @api.depends('order_line.exchange_rate_applied')
    def _compute_exchange_rate_buttons(self):
        for rec in self:
            lines = rec.order_line

            rec.can_apply_exchange_rate = any(
                not line.exchange_rate_applied
                for line in lines
            )

            rec.can_undo_exchange_rate = any(
                line.exchange_rate_applied
                for line in lines
            )
    
    def exchange_rate_lines_wizard_action(self):
        for rec in self:
            
            action = self.env.context.get('action', False)
            if rec.state != 'draft' or not action:
                continue
            
            return {
                'name': (_('Apply Exchange Rate')) if action == 'apply' else (_('Undo Exchange Rate')),
                'type': 'ir.actions.act_window',
                'res_model': 'apply.exchange.rate.purchase.order.lines.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('pao_exchange_rate_option.apply_exchange_rate_purchase_order_lines_wizard_form').id,
                'target': 'new',
                'context': {
                    'default_order_id': self.id,
                    'undo_action': action == 'undo'
                },
            }
            
class PurchaseOrderLineInherit(models.Model):

    _inherit='purchase.order.line'
    
    exchange_rate_applied = fields.Boolean(default=False, copy=False)
    exchange_rate_value = fields.Float(copy=False)