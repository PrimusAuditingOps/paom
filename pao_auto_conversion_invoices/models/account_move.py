from odoo import models, fields, api, _
from logging import getLogger

_logger = getLogger(__name__)

class AccountMoveInherit(models.Model):

    _inherit='account.move'
    
    auto_conversion_applied = fields.Boolean(default=False, copy=False)
    
    can_undo_conversion = fields.Boolean(
        compute='_compute_can_undo_conversion'
    )

    @api.depends('invoice_line_ids.exchange_rate_applied')
    def _compute_can_undo_conversion(self):
        for move in self:
            lines = move.invoice_line_ids

            move.can_undo_conversion = any(
                line.exchange_rate_applied
                for line in lines
            )
    

    @api.onchange('currency_id')
    def _onchange_currency_id_prompt_wizard(self):
        _logger.warning("ONCHANGE")
        if self.company_id.id != 1 or self.auto_conversion_applied:
            return
        
        # Only trigger when changing from USD to MXN
        usd = self.env.ref('base.USD', raise_if_not_found=False)
        mxn = self.env.ref('base.MXN', raise_if_not_found=False)
        
        _logger.warning(str(usd) + " - " + str(mxn))

        if not usd or not mxn:
            return

        origin = self._origin.currency_id  # currency before the change
        
        _logger.warning("Origin: " + str(origin))
        
        _logger.warning("ONCHANGE 2")

        if origin == usd and self.currency_id == mxn:
            _logger.warning("ONCHANGE 3")
            # return {
            #     # 'name': (_('Apply Exchange Rate')) if action == 'apply' else (_('Undo Exchange Rate')),
            #     'type': 'ir.actions.act_window',
            #     'res_model': 'auto.currency.conversion.wizard',
            #     'view_mode': 'form',
            #     'view_id': self.env.ref('pao_auto_conversion_invoices.auto_currency_conversion_wizard_form').id,
            #     'target': 'new',
            #     'context': {
            #         'default_move_id': self._origin.id,
            #         'default_from_currency_id': usd.id,
            #         'default_to_currency_id': mxn.id,
            #     },
            # }
            return {'warning': {
                'title': _("TEST 1"),
                'message': _("TEST 2."),
            }}
            
# class AccountMoveLineInherit(models.Model):

#     _inherit='account.move.line'
    
#     exchange_rate_applied = fields.Boolean(default=False, copy=False)
#     exchange_rate_value = fields.Float(copy=False)
    
# class ProductProductInherit(models.Model):

#     _inherit='product.product'
    
#     country_code = fields.Char(related='company_id.country_code')
    
#     def _default_base_currency(self):
#         company = self.env.company
#         if company.country_id and company.country_id.code == 'CL':
#             return self.env.ref('base.USD', raise_if_not_found=False)
#         return False
    
#     base_currency_id = fields.Many2one('res.currency', string="Base Currency", default=_default_base_currency, copy=False)
    
#     def update_base_currencies_chilean_products(self):
#         usd = self.env.ref('base.USD', raise_if_not_found=False)
#         if not usd:
#             return False

#         products = self.search([
#             ('country_code', '=', 'CL'),
#             ('base_currency_id', '=', False),
#         ])

#         products.write({
#             'base_currency_id': usd.id
#         })

#         return True
        