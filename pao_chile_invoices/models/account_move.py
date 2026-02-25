from odoo import models, fields, api, _

class AccountMoveInherit(models.Model):

    _inherit='account.move'
    
    # auto_exchange_rate_lines_value = fields.Float(string="Exchange Rate", copy=False)
    
    # exchange_rate_applied = fields.Boolean(default=False, copy=False)
    
    # def apply_exchange_rate_lines_action(self):
    #     for move in self:
    #         rate = move.auto_exchange_rate_lines_value

    #         if move.state != 'draft' or not rate or move.exchange_rate_applied:
    #             continue

    #         for line in move.invoice_line_ids:
    #             if line.price_unit:
    #                 new_price = line.price_unit * rate
    #                 line.price_unit = new_price
                    
    #         move.exchange_rate_applied = True
    
    # def undo_exchange_rate_lines_action(self):
    #     for move in self:
    #         rate = move.auto_exchange_rate_lines_value

    #         if move.state != 'draft' or not rate or not move.exchange_rate_applied:
    #             continue 

    #         for line in move.invoice_line_ids:
    #             if line.price_unit:
    #                 new_price = line.price_unit / rate
    #                 line.price_unit = new_price
                    
    #         move.exchange_rate_applied = False
    
    can_apply_exchange_rate = fields.Boolean(
        compute='_compute_exchange_rate_buttons'
    )
    can_undo_exchange_rate = fields.Boolean(
        compute='_compute_exchange_rate_buttons'
    )

    @api.depends('invoice_line_ids.exchange_rate_applied')
    def _compute_exchange_rate_buttons(self):
        for move in self:
            lines = move.invoice_line_ids

            move.can_apply_exchange_rate = any(
                not line.exchange_rate_applied
                for line in lines
            )

            move.can_undo_exchange_rate = any(
                line.exchange_rate_applied
                for line in lines
            )
    
    def exchange_rate_lines_wizard_action(self):
        for move in self:
            
            action = self.env.context.get('action', False)
            if move.state != 'draft' or not action:
                continue
            
            return {
                'name': (_('Apply Exchange Rate')) if action == 'apply' else (_('Undo Exchange Rate')),
                'type': 'ir.actions.act_window',
                'res_model': 'apply.exchange.rate.move.lines.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('pao_chile_invoices.apply_exchange_rate_move_lines_wizard_form').id,
                'target': 'new',
                'context': {
                    'default_move_id': self.id,
                    'undo_action': action == 'undo'
                },
            }
            
    def remove_fee_lines_action(self):
        for move in self:
            fee_lines = move.invoice_line_ids.filtered(
                lambda line: line.name and line.name.startswith('FEE ')
            )
            if fee_lines:
                fee_lines.unlink()
            
class AccountMoveLineInherit(models.Model):

    _inherit='account.move.line'
    
    exchange_rate_applied = fields.Boolean(default=False, copy=False)
    exchange_rate_value = fields.Float(copy=False)
    
class ProductProductInherit(models.Model):

    _inherit='product.product'
    
    country_code = fields.Char(related='company_id.country_code')
    
    def _default_base_currency(self):
        company = self.env.company
        if company.country_id and company.country_id.code == 'CL':
            return self.env.ref('base.USD', raise_if_not_found=False)
        return False
    
    base_currency_id = fields.Many2one('res.currency', string="Base Currency", default=_default_base_currency, copy=False)