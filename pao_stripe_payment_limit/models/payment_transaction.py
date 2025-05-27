from odoo import models, _
from logging import getLogger

_logger = getLogger(__name__)
class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    def _create_payment_vals(self, invoice):
            vals = super()._create_payment_vals(invoice)
            _logger.warning("ENTRA*******************")
            _logger.warning(self.provider_id.code)
            if self.provider_id.code == 'stripe':
                custom_ref = (f'{self.reference}')
                vals['ref'] = custom_ref
            return vals