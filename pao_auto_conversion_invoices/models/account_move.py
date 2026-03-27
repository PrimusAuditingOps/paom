from odoo import models, fields, api, _
from logging import getLogger

_logger = getLogger(__name__)

class AccountMoveInherit(models.Model):

    _inherit='account.move'
    
    auto_conversion_applied = fields.Boolean(default=False, copy=False)
    can_auto_convert = fields.Boolean(default=False, copy=False)
    
    def apply_auto_convert_to_mxn(self):
        if not self.can_auto_convert or self.company_id.id != 1 or self.auto_conversion_applied or self.state != 'draft':
            return

        usd = self.env.ref('base.USD', raise_if_not_found=False)
        mxn = self.env.ref('base.MXN', raise_if_not_found=False)

        if not usd or not mxn:
            return

        date = self.invoice_date or fields.Date.today()
        if not date:
            return {'warning': {
                'title': _("Exchange Rate Not Available"),
                'message': _("No exchange rate was found for the invoice date or the current date. Please make sure a valid exchange rate exists for the selected currencies before proceeding"),
            }}

        rate = usd._get_conversion_rate(usd, mxn, self.company_id, date)
        for line in self.invoice_line_ids:
            line.price_unit = usd._convert(
                line.price_unit,
                mxn,
                self.company_id,
                date,
            )
            line.exchange_rate_value = rate
            line.exchange_rate_applied = True

        self.auto_conversion_applied = True
        self.can_auto_convert = False
        
    def undo_auto_convert_to_mxn(self):
        if not self.auto_conversion_applied or self.state != 'draft':
            return

        for line in self.invoice_line_ids:
            if line.exchange_rate_applied:
                # Reverse: MXN / rate = USD
                line.price_unit /= line.exchange_rate_value
                line.exchange_rate_applied = False
                line.exchange_rate_value = None
                
        self.auto_conversion_applied = False

    @api.onchange('currency_id')
    def _onchange_currency_id_activate_auto_convert(self):
        if self.company_id.id != 1 or self.auto_conversion_applied or self.state != 'draft':
            return
        
        self.can_auto_convert = False
        
        # Only trigger when changing from USD to MXN
        usd = self.env.ref('base.USD', raise_if_not_found=False)
        mxn = self.env.ref('base.MXN', raise_if_not_found=False)
        
        if not usd or not mxn:
            return

        origin = self._origin.currency_id  # currency before the change
        
        if origin == usd and self.currency_id == mxn:
            self.can_auto_convert = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('Price Conversion Available'),
                    'message': _('The invoice currency has been changed from USD to MXN. Use the "Convert Prices" button to automatically apply the exchange rate to the invoice lines.'),
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }