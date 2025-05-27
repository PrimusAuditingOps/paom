from odoo import models, _

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _create_payment(self, **extra_create_values):
            """Create an `account.payment` record for the current transaction.

            If the transaction is linked to some invoices, their reconciliation is done automatically.

            Note: self.ensure_one()

            :param dict extra_create_values: Optional extra create values
            :return: The created payment
            :rtype: recordset of `account.payment`
            """
            self.ensure_one()

            if self.provider_id.code == 'stripe':
                reference = (f'{self.reference}')
            else:
                reference = (f'{self.reference} - '
                            f'{self.partner_id.display_name or ""} - '
                            f'{self.provider_reference or ""}'
                            )

            payment_method_line = self.provider_id.journal_id.inbound_payment_method_line_ids\
                .filtered(lambda l: l.payment_provider_id == self.provider_id)
            payment_values = {
                'amount': abs(self.amount),  # A tx may have a negative amount, but a payment must >= 0
                'payment_type': 'inbound' if self.amount > 0 else 'outbound',
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.commercial_partner_id.id,
                'partner_type': 'customer',
                'journal_id': self.provider_id.journal_id.id,
                'company_id': self.provider_id.company_id.id,
                'payment_method_line_id': payment_method_line.id,
                'payment_token_id': self.token_id.id,
                'payment_transaction_id': self.id,
                'ref': reference,
                **extra_create_values,
            }
            payment = self.env['account.payment'].create(payment_values)
            payment.action_post()

            # Track the payment to make a one2one.
            self.payment_id = payment

            # Reconcile the payment with the source transaction's invoices in case of a partial capture.
            if self.operation == self.source_transaction_id.operation:
                invoices = self.source_transaction_id.invoice_ids
            else:
                invoices = self.invoice_ids
            if invoices:
                invoices.filtered(lambda inv: inv.state == 'draft').action_post()

                (payment.line_ids + invoices.line_ids).filtered(
                    lambda line: line.account_id == payment.destination_account_id
                    and not line.reconciled
                ).reconcile()

            return payment