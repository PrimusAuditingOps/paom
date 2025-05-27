from odoo import models, _
from logging import getLogger

_logger = getLogger(__name__)
class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _create_payment(self, **extra_create_values):
        payment = super()._create_payment(extra_create_values)
        
        _logger.warning(payment)
        
        _logger.warning("ENTRA****")
        
        _logger.warning(self.provider_id.code)
        
        _logger.warning("****************")

        if self.provider_id.code == 'stripe':
            reference = (f'{self.reference}')
            _logger.warning(reference)
            payment.ref = reference

        return payment