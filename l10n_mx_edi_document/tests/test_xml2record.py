# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from os.path import join
from odoo.tools import misc

from odoo.tests.common import Form
from odoo.tests.common import TransactionCase


class Xml2Record(TransactionCase):

    def setUp(self):
        super(Xml2Record, self).setUp()
        self.rule = self.env.ref('l10n_mx_edi_document.mexican_document_rule')
        self.invoice_xml = misc.file_open(join(
            'l10n_mx_edi_document', 'tests', 'invoice.xml')).read().encode(
                'UTF-8')
        self.payment_xml = misc.file_open(join(
            'l10n_mx_edi_document', 'tests', 'payment.xml')).read().encode(
                'UTF-8')
        self.finance_folder = self.env.ref(
            'documents.documents_finance_folder')
        self.env.ref('product.product_product_4d').unspsc_code_id = self.env.ref(
            'product_unspsc.unspsc_code_01010101')

    def test_invoice_payment(self):
        """The invoice must be generated based in the payment, after the
        payment must be reconciled with the invoice"""
        attachment = self.env['ir.attachment'].create({
            'name': 'invoice.xml',
            'datas': base64.b64encode(self.invoice_xml),
            'description': 'Mexican invoice',
        })
        invoice_document = self.env['documents.document'].create({
            'name': attachment.name,
            'folder_id': self.finance_folder.id,
            'attachment_id': attachment.id
        })
        invoice = self.rule.create_record(invoice_document).get('res_id')
        attachment = attachment.create({
            'name': 'payment.xml',
            'datas': base64.b64encode(self.payment_xml),
            'description': 'Mexican payment',
        })
        payment_document = self.env['documents.document'].create({
            'name': attachment.name,
            'folder_id': self.finance_folder.id,
            'attachment_id': attachment.id
        })
        self.rule.create_record(payment_document)
        self.assertEqual(
            self.env['account.move'].browse(invoice).payment_state, 'paid', 'Invoice was not paid')

    def test_payment_existent(self):
        """If the payment is found, not must be created a new."""
        attachment = self.env['ir.attachment'].create({
            'name': 'invoice.xml',
            'datas': base64.b64encode(self.invoice_xml),
            'description': 'Mexican invoice',
        })
        invoice_document = self.env['documents.document'].create({
            'name': attachment.name,
            'folder_id': self.finance_folder.id,
            'attachment_id': attachment.id
        })
        invoice = self.rule.create_record(invoice_document).get('res_id')
        invoice = self.env['account.move'].browse(invoice)
        self.assertEqual(invoice.edi_state, 'sent', invoice.message_ids.mapped('body'))

        self.bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank')], limit=1)
        invoice.refresh()
        payment_register = Form(self.env['account.payment'].with_context(
            active_model='account.move', active_ids=invoice.ids, default_date=invoice.invoice_date))
        payment_register.payment_method_id = self.env.ref("account.account_payment_method_manual_in")
        payment_register.journal_id = self.bank_journal
        payment_register.amount = invoice.amount_total
        payment_register.partner_id = invoice.partner_id
        payment = payment_register.save()
        payment.action_post()
        lines = payment.move_id.line_ids.filtered(
            lambda line: line.account_id.internal_type in ('receivable', 'payable'))
        lines |= invoice.line_ids.filtered(
            lambda line: line.account_id in lines.mapped('account_id') and not line.reconciled)
        lines.reconcile()
        attachment = attachment.create({
            'name': 'payment.xml',
            'datas': base64.b64encode(self.payment_xml),
            'description': 'Mexican payment',
        })
        payment_document = self.env['documents.document'].create({
            'name': attachment.name,
            'folder_id': self.finance_folder.id,
            'attachment_id': attachment.id
        })
        new_payment = self.rule.create_record(payment_document).get('res_id')
        self.assertEqual(
            payment.id, new_payment,
            'A new payment was created, that is incorrect')

    def test_payment_not_existent(self):
        """2 payments created."""
        attachment = self.env['ir.attachment'].create({
            'name': 'invoice.xml',
            'datas': base64.b64encode(self.invoice_xml),
            'description': 'Mexican invoice',
        })
        invoice_document = self.env['documents.document'].create({
            'name': attachment.name,
            'folder_id': self.finance_folder.id,
            'attachment_id': attachment.id
        })
        invoice = self.rule.create_record(invoice_document).get('res_id')
        attachment = attachment.create({
            'name': 'payment.xml',
            'datas': base64.b64encode(self.payment_xml),
            'description': 'Mexican payment',
        })
        payment_document = self.env['documents.document'].create({
            'name': attachment.name,
            'folder_id': self.finance_folder.id,
            'attachment_id': attachment.id
        })
        payment = self.rule.create_record(payment_document).get('res_id')
        self.env['account.payment'].browse(payment).refresh()
        new_xml = self.payment_xml.replace(b'UUID="0', b'UUID="1')
        attachment = attachment.create({
            'name': 'payment.xml',
            'datas': base64.b64encode(new_xml),
            'description': 'Mexican payment',
        })
        payment_document = self.env['documents.document'].create({
            'name': attachment.name,
            'folder_id': self.finance_folder.id,
            'attachment_id': attachment.id
        })
        new_payment = self.rule.create_record(payment_document).get('res_id')
        self.assertNotEqual(payment, new_payment, 'Both payments are the same')
        self.assertEqual(
            self.env['account.move'].browse(invoice).payment_state, 'paid', 'Invoice was not paid')

    def test_payment_not_created(self):
        """Avoid payment creation."""
        self.env['ir.config_parameter'].create({
            'key': 'mexico_document_avoid_create_payment',
            'value': True})
        attachment = self.env['ir.attachment'].create({
            'name': 'payment.xml',
            'datas': base64.b64encode(self.payment_xml),
            'store_fname': 'payment.xml',
            'description': 'Mexican payment',
        })
        payment_document = self.env['documents.document'].create({
            'name': attachment.name,
            'folder_id': self.finance_folder.id,
            'attachment_id': attachment.id
        })
        payment = self.rule.create_record(payment_document).get('res_id')
        self.assertFalse(
            payment, 'The payment was created with the system parameter')

    def test_invoice_duplicated(self):
        """The invoice must be generated only one time"""
        attachment = self.env['ir.attachment'].create({
            'name': 'invoice.xml',
            'datas': base64.b64encode(self.invoice_xml),
            'description': 'Mexican invoice',
        })
        invoice_document = self.env['documents.document'].create({
            'name': attachment.name,
            'folder_id': self.finance_folder.id,
            'attachment_id': attachment.id
        })
        invoice = self.rule.create_record(invoice_document).get('res_id')
        attachment = self.env['ir.attachment'].create({
            'name': 'invoice.xml',
            'datas': base64.b64encode(self.invoice_xml),
            'description': 'Mexican invoice',
        })
        invoice_document = invoice_document.copy({
            'attachment_id': attachment.id
        })
        invoice2 = self.rule.create_record(invoice_document).get('res_id')
        self.assertEqual(invoice, invoice2, 'Invoice generated 2 times.')
