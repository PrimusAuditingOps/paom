from odoo import api, exceptions, fields, models, _
from logging import getLogger

_logger = getLogger(__name__)

class AccountPayment(models.Model):
    _inherit='account.payment'
    
    pao_invoices_sage_folio = fields.Char(
        string = 'folios SAGE',
        compute = '_get_sage_folios',
    )  


    def _get_sage_folios(self):
        
        for rec in self:
            folios = ""
            sql = """
                SELECT  ARRAY_AGG(DISTINCT invoice.pao_sage_folio) as invoiceids
                FROM account_payment payment
                JOIN account_move move ON move.id = payment.move_id
                JOIN account_move_line line ON line.move_id = move.id
                JOIN account_partial_reconcile part ON
                part.debit_move_id = line.id
                OR
                part.credit_move_id = line.id
                JOIN account_move_line counterpart_line ON
                part.debit_move_id = counterpart_line.id
                OR
                part.credit_move_id = counterpart_line.id
                JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                JOIN account_account account ON account.id = line.account_id
                WHERE account.internal_type IN ('receivable', 'payable')
                AND payment.id = %(payment_ids)s
                AND line.id != counterpart_line.id
                AND invoice.move_type in ('out_invoice')
                GROUP BY payment.id, invoice.move_type
                """
            params = {'payment_ids': rec.id}
            rec.env.cr.execute(sql, params)
            result = rec.env.cr.dictfetchall()
            for inv in result:
                for sage in inv['invoiceids']:
                    if folios == "":
                        folios += str(sage)
                    else:
                        folios+= ", " + str(sage) 

            rec.pao_invoices_sage_folio = folios