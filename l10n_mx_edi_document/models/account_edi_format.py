from odoo import models


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _is_required_for_invoice(self, invoice):
        """Avoid generate a new CFDI"""
        if invoice.edi_state == 'sent':
            return False
        return super(AccountEdiFormat, self)._is_required_for_invoice(invoice)
