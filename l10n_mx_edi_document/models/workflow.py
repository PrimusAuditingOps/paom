from os.path import splitext
from odoo import models, fields


class WorkflowActionRuleAccount(models.Model):
    _inherit = ['documents.workflow.rule']

    create_model = fields.Selection(
        selection_add=[
            ('l10n_mx_edi.mexican.document', "Mexican Document")])

    def create_record(self, documents=None):
        rv = super(WorkflowActionRuleAccount, self).create_record(
            documents=documents)
        if self.create_model != 'l10n_mx_edi.mexican.document' or not documents:  # noqa
            return rv
        document_ids = []
        body = "<p>created with DMS</p>"
        incorrect_folder = self.env.ref(
            'l10n_mx_edi_document.documents_incorrect_cfdis_folder', False)
        rule_tc = self.env.ref('documents.documents_rule_finance_validate')
        for document in documents.filtered(
            lambda doc: not doc.res_id or
                doc.res_model == 'documents.document'):
            if splitext(document.name)[1].upper() != '.XML':
                continue
            attachment_id = document.attachment_id
            document_type, res_model = attachment_id.l10n_mx_edi_document_type()
            if not document_type:
                document.res_model = False
                document.tag_ids = False
                rule_tc.apply_actions(document.ids)
                document.folder_id = incorrect_folder
                document.message_post(body=res_model.get('error'))
                continue
            create_values = {}

            # TODO - Allow set the journal for each model
            if res_model == 'account.payment':
                journal = self.env['account.journal'].search(
                    [('type', 'in', ('bank', 'cash'))], limit=1)
                create_values.update({
                    'payment_type': 'inbound' if document_type == 'customerP' else 'outbound',  # noqa
                    'partner_type': 'customer' if document_type == 'customerP' else 'supplier',  # noqa
                    'payment_method_id': (journal.inbound_payment_method_ids[
                        0] if document_type == 'customerP' else
                        journal.outbound_payment_method_ids[0]).id,
                    'amount': 0,
                    'journal_id': journal.id,
                })
            elif res_model == 'account.move':
                invoice_type = {'customerI': 'out_invoice',
                                'customerE': 'out_refund',
                                'vendorI': 'in_invoice',
                                'vendorE': 'in_refund'}.get(document_type)
                journal = self.env['account.move'].with_context(
                    {'default_move_type': invoice_type})._get_default_journal()
                create_values.update({
                    'move_type': invoice_type,
                    'journal_id': journal.id,
                })
            result = self.env[res_model].create(create_values)
            document_ids.append(result.id)
            result.with_context(no_new_invoice=True).message_post(
                body=body, attachment_ids=[attachment_id.id])
            this_attachment = attachment_id
            if attachment_id.res_model or attachment_id.res_id:
                this_attachment = attachment_id.copy()
                document.attachment_id = this_attachment.id

            this_attachment.write({
                'res_model': res_model,
                'res_id': result.id,
            })

            document_ids.append(result.id)
            result = result.xml2record()
            result.l10n_mx_edi_update_sat_status()
            document.toggle_active()

        if not document_ids:
            return rv
        action = {
            'type': 'ir.actions.act_window',
            'res_model': result._name,
            'name': "Mexican Documents",
            'view_id': False,
            'view_type': 'list',
            'view_mode': 'tree',
            'views': [(False, "list"), (False, "form")],
            'domain': [('id', 'in', document_ids)],
            'context': self._context,
        }
        if len(documents) == 1 and result:
            view_id = result.get_formview_id() if result else False
            action.update({
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, "form")],
                'res_id': result.id if result else False,
                'view_id': view_id,
            })
        return action
