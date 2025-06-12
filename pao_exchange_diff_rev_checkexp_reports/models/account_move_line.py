from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'


    pao_exchange_difference_vendor = fields.Boolean(
        string="Is a Exchange Difference from Vendor",
        default = False,
        compute="_get_pao_exchange_difference_vendor",
        store=True,
    )
    pao_exchange_difference_customer = fields.Boolean(
        string="Is a Exchange Difference from Customer",
        default = False,
        compute="_get_pao_exchange_difference_Customer",
        store=True,
    )
    
    @api.depends("move_id")
    def _get_pao_exchange_difference_vendor(self):
        for rec in self:
            rec.pao_exchange_difference_vendor = False
            if rec.journal_id.id == 4:
                ids = rec.move_id.line_ids._all_reconciled_lines().filtered(lambda l: l.matched_debit_ids or l.matched_credit_ids).ids
                rec_data = rec.env["account.move.line"].search([('id', 'in', ids), ('move_name', 'ilike', "BILL")])
                rec_data_account = rec.env["account.move.line"].search([('id', 'in', ids), ('account_id', '=', 7050)])
                if rec_data:
                    rec.pao_exchange_difference_vendor = True
                elif rec_data_account:
                    rec.pao_exchange_difference_vendor = True

    @api.depends("move_id")
    def _get_pao_exchange_difference_Customer(self):
        for rec in self:
            rec.pao_exchange_difference_customer = False
            if rec.journal_id.id == 4:
                ids = rec.move_id.line_ids._all_reconciled_lines().filtered(lambda l: l.matched_debit_ids or l.matched_credit_ids).ids
                rec_data = rec.env["account.move.line"].search([('id', 'in', ids), ('move_name', 'ilike', "INV")])
                rec_data_account = rec.env["account.move.line"].search([('id', 'in', ids), ('account_id', 'in', [3,20,7056])])
                if rec_data:
                    rec.pao_exchange_difference_customer = True
                elif rec_data_account:
                    rec.pao_exchange_difference_customer = True
                elif not ids:
                    ids = rec.move_id.line_ids.filtered(lambda l: l.account_id.id == 3).ids
                    if ids:
                        rec.pao_exchange_difference_customer = True
            if rec.journal_id.id == 6:
                ids = rec.move_id.line_ids._all_reconciled_lines().filtered(lambda l: l.matched_debit_ids or l.matched_credit_ids).ids
                rec_data = rec.env["account.move.line"].search([('id', 'in', ids), ('move_name', 'ilike', "INV")])
                rec_data_account = rec.env["account.move.line"].search([('id', 'in', ids), ('account_id', 'in', [3,20,7056])])
                if rec_data:
                    rec.pao_exchange_difference_customer = True
                elif rec_data_account:
                    rec.pao_exchange_difference_customer = True
                elif not ids:
                    ids = rec.move_id.line_ids.filtered(lambda l: l.account_id.id == 3).ids
                    if ids:
                        rec.pao_exchange_difference_customer = True

