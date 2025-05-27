from odoo import models, api
from logging import getLogger
_logger = getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def create(self, vals):
        _logger.warning("ENTRAAAAAAAA********************")
        if vals.get('payment_transaction_id'):
            transaction = self.env['payment.transaction'].browse(vals['payment_transaction_id'])
            if transaction.provider_id.code == 'stripe':
                vals['ref'] = transaction.reference
        return super(AccountPayment, self).create(vals)