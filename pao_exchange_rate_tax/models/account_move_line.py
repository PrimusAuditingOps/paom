# -*- coding: utf-8 -*-
from odoo import api, models, Command, _
from odoo.exceptions import UserError
from collections import defaultdict


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _prepare_exchange_difference_move_vals(self, amounts_list, company=None, exchange_date=None, **kwargs):
        """ Super, assign ref with invoice name """
        res = super(AccountMoveLine, self)._prepare_exchange_difference_move_vals(amounts_list, company, exchange_date, **kwargs)
        if res.get('move_values'):
            res.get('move_values')['ref'] = self.get_invoice_reference()
        return res

    def get_invoice_reference(self):
        """ Get list of invoice name """
        # Try to get related sale order from stock moves
        move_ids = self.mapped('move_id')
        result = ''
        if move_ids:
            # If multiple SOs, join their name
            list_name = [name for name in move_ids.mapped('display_name') if name]
            if list_name:
                result = ', '.join(list_name)
        return result
    
    @api.model
    def _create_exchange_difference_moves(self, exchange_diff_values_list):
        """
        OVERRIDE to add tax adjustment lines to exchange entries.
        
        Handles TWO scenarios:
        1. POSITIVE (partial payment): Modify vals BEFORE create
        2. NEGATIVE (overpayment): Modify moves AFTER create, BEFORE post
        """
        # STEP 1: POSITIVE SCENARIO - Modify vals before create
        for exchange_diff_values in exchange_diff_values_list:
            self._add_tax_adjustment_to_exchange_vals(
                exchange_diff_values
            )
        
        # ===== DUPLICATE LOGIC FROM SUPER =====
        # (We need full control between create and post)
        
        exchange_move_values_list = []
        journal_ids = set()
        for exchange_diff_values in exchange_diff_values_list:
            move_vals = exchange_diff_values['move_values']
            exchange_move_values_list.append(move_vals)

            if not move_vals['journal_id']:
                raise UserError(_(
                    "You have to configure the 'Exchange Gain or Loss Journal' in your company settings, to manage"
                    " automatically the booking of accounting entries related to differences between exchange rates."
                ))

            journal_ids.add(move_vals['journal_id'])

        if not exchange_move_values_list:
            return self.env['account.move']

        # ==== Check the config ====
        journals = self.env['account.journal'].browse(list(journal_ids))
        for journal in journals:
            if not journal.company_id.expense_currency_exchange_account_id:
                raise UserError(_(
                    "You should configure the 'Loss Exchange Rate Account' in your company settings, to manage"
                    " automatically the booking of accounting entries related to differences between exchange rates."
                ))
            if not journal.company_id.income_currency_exchange_account_id.id:
                raise UserError(_(
                    "You should configure the 'Gain Exchange Rate Account' in your company settings, to manage"
                    " automatically the booking of accounting entries related to differences between exchange rates."
                ))

        # ==== Create the move ====
        exchange_moves = self.env['account.move'].create(exchange_move_values_list)
        
        # STEP 2: NEGATIVE SCENARIO - Modify moves AFTER create, BEFORE post
        for move in exchange_moves:
            if self._is_negative_exchange_scenario(move):
                self._handle_negative_exchange_tax_split(move)
        
        # ==== Post the moves ====
        exchange_moves._post(soft=False)

        # ==== Reconcile ====
        reconciliation_plan = []
        for exchange_move, exchange_diff_values in zip(exchange_moves, exchange_diff_values_list):
            for source_line, sequence in exchange_diff_values['to_reconcile']:
                exchange_diff_line = exchange_move.line_ids[sequence]
                reconciliation_plan.append((source_line + exchange_diff_line))

        self\
            .with_context(no_exchange_difference=True)\
            ._reconcile_plan(reconciliation_plan)

        return exchange_moves
    
    def _add_tax_adjustment_to_exchange_vals(
        self, exchange_diff_vals
    ):
        """
        Add tax adjustment lines to exchange_diff_vals
        if there are cash basis taxes that need adjustment.
        """
        # Get lines from to_reconcile
        if not exchange_diff_vals.get('to_reconcile'):
            return
        
        # Check if exchange lines have actual amounts
        # Skip if all exchange lines are zero (no actual exchange difference)
        move_vals = exchange_diff_vals.get('move_values', {})
        line_ids = move_vals.get('line_ids', [])
        
        has_exchange_amount = False
        for line_cmd in line_ids:
            if line_cmd[0] == 0:  # Command.create
                line_vals = line_cmd[2]
                debit = line_vals.get('debit', 0)
                credit = line_vals.get('credit', 0)
                # Exchange line has non-zero debit OR credit (not both)
                if (debit > 0 and credit == 0) or (credit > 0 and debit == 0):
                    has_exchange_amount = True
                    break
        
        # Skip if no exchange amount (empty exchange entry)
        if not has_exchange_amount:
            return
        
        # Extract move lines from to_reconcile tuples
        lines = self.env['account.move.line'].browse([
            line.id for line, sequence in exchange_diff_vals['to_reconcile']
        ])
        
        # Check if we should apply tax fix
        if not lines._should_apply_pao_exchange_rate_tax_fix():
            return
        
        # Get payment rates
        payment_rates_map = lines._get_payment_rates_by_invoice()
        
        # Add tax adjustment lines
        lines._pao_add_exchange_diff_cash_basis(
            exchange_diff_vals,
            payment_rates_map
        )

    def _should_apply_pao_exchange_rate_tax_fix(self):
        """
        Check if the custom tax fix should be applied.
        
        Returns True if:
        1. There are invoices with cash basis taxes involved
        2. Company has tax exigibility enabled
        3. There are CABA entries (existing or to be processed)
        """
        # Check if any of the moves have cash basis taxes
        for move in self.move_id:
            if not move.is_invoice(include_receipts=True):
                continue
            
            # Check for cash basis tax lines on the invoice
            has_cash_basis_tax = any(
                line.tax_line_id and 
                line.tax_line_id.tax_exigibility == 'on_payment'
                for line in move.line_ids
            )
            
            if not has_cash_basis_tax:
                continue
            
            # Check if there are EXISTING CABA entries
            existing_caba = self.env['account.move'].search([
                ('tax_cash_basis_origin_move_id', '=', move.id)
            ], limit=1)
            
            if existing_caba:
                return True
            
            # OR check if there are pending CABA to process
            move_values = move._collect_tax_cash_basis_values()
            if move_values and move_values.get('to_process_lines'):
                return True
        
        return False
    
    def _get_payment_rates_by_invoice(self):
        """
        Get payment rates from partial reconcile records, organized by invoice.
        
        Returns a dictionary mapping invoice_move_id to payment_rate.
        For multiple payments, uses weighted average or most recent rate.
        """
        payment_rates = {}
        
        for line in self:
            if line.move_id.is_invoice(include_receipts=True):
                invoice_move = line.move_id
                
                # Get all partials for this invoice
                invoice_lines = invoice_move.line_ids.filtered(
                    lambda l: l.account_type in ('asset_receivable', 'liability_payable')
                )
                
                all_partials = invoice_lines.mapped('matched_debit_ids') + invoice_lines.mapped('matched_credit_ids')
                
                if not all_partials:
                    continue
                
                # Calculate weighted average payment rate or use most recent
                total_amount = 0.0
                weighted_rate = 0.0
                latest_date = False
                latest_rate = 0.0
                
                for partial in all_partials:
                    # Determine which line is invoice and which is payment
                    if partial.debit_move_id.move_id == invoice_move:
                        invoice_line = partial.debit_move_id
                        payment_line = partial.credit_move_id
                        partial_amount = partial.amount
                    elif partial.credit_move_id.move_id == invoice_move:
                        invoice_line = partial.credit_move_id
                        payment_line = partial.debit_move_id
                        partial_amount = partial.amount
                    else:
                        continue
                    
                    # Calculate payment rate for this partial
                    if invoice_line.currency_id != payment_line.currency_id:
                        # Different currencies
                        payment_rate = self.env['res.currency']._get_conversion_rate(
                            payment_line.company_currency_id,
                            invoice_line.currency_id,
                            payment_line.company_id,
                            payment_line.date,
                        )
                    else:
                        # Same currency - calculate from amounts
                        if payment_line.balance:
                            payment_rate = abs(payment_line.amount_currency / payment_line.balance)
                        else:
                            payment_rate = 1.0
                    
                    # Track for weighted average
                    total_amount += partial_amount
                    weighted_rate += partial_amount * payment_rate
                    
                    # Track most recent
                    payment_date = payment_line.date
                    if not latest_date or payment_date > latest_date:
                        latest_date = payment_date
                        latest_rate = payment_rate
                
                # Use weighted average if available, otherwise most recent
                if total_amount:
                    final_rate = weighted_rate / total_amount
                elif latest_rate:
                    final_rate = latest_rate
                else:
                    final_rate = 1.0
                
                payment_rates[invoice_move.id] = final_rate

        return payment_rates

    def _pao_add_exchange_diff_cash_basis(
        self,
        exchange_diff_vals,
        payment_rates_map
    ):
        """
        Modified version that creates tax adjustment lines in exchange
        entry to ensure 100% of tax goes to tax accounts.
        """
        caba_lines_to_reconcile = defaultdict(
            lambda: self.env['account.move.line']
        )
        move_vals = exchange_diff_vals['move_values']
        
        # Collect ALL tax adjustments from ALL moves
        all_tax_adjustments = {}

        for move in self.move_id:
            move_values = move._collect_tax_cash_basis_values()

            if not move_values or not move_values['is_fully_paid']:
                continue

            move_vals['date'] = max(move_vals['date'], move.date)

            # Collect EXPECTED tax from INVOICE
            for line in move.line_ids:
                # Only process tax lines with on_payment exigibility
                if (line.tax_line_id and 
                    line.tax_line_id.tax_exigibility == 'on_payment' and
                    line.tax_repartition_line_id):
                    
                    # Get the FINAL tax account (where tax should go)
                    tax_account = (
                        line.tax_repartition_line_id.account_id
                    )
                    
                    if not tax_account:
                        continue
                    
                    tax_key = (
                        line.tax_repartition_line_id.id,
                        tax_account.id,
                    )

                    if tax_key not in all_tax_adjustments:
                        all_tax_adjustments[tax_key] = {
                            'expected_amount_currency': 0.0,
                            'tax_repartition_line': (
                                line.tax_repartition_line_id
                            ),
                            'tax_account': tax_account,
                            'currency': line.currency_id,
                            'partner_id': line.partner_id.id,
                            'tax_ids': line.tax_ids.ids,
                            'tax_tag_ids': line.tax_tag_ids.ids,
                        }

                    # Accumulate expected tax amount from invoice
                    tax_amount_on_invoice = line.balance
                    all_tax_adjustments[tax_key][
                        'expected_amount_currency'
                    ] += tax_amount_on_invoice


        # Split exchange difference proportionally between base and tax
        existing_line_vals_list = move_vals['line_ids']
        next_sequence = len(existing_line_vals_list)
        
        # Find exchange account line (the one with gain/loss account)
        exchange_line_vals = None
        
        exchange_accounts = [
            self.company_id.income_currency_exchange_account_id.id,
            self.company_id.expense_currency_exchange_account_id.id
        ]
        
        for line_cmd in existing_line_vals_list:
            if line_cmd[0] == 0:  # Command.create
                line_vals = line_cmd[2]
                # Detect exchange line by account_id (not by name string)
                if (line_vals.get('account_id') in exchange_accounts and
                    not line_vals.get('full_reconcile_id')):
                    exchange_line_vals = line_vals
                    break
        
        # Skip if no exchange line or no tax adjustments
        if not exchange_line_vals or not all_tax_adjustments:
            return caba_lines_to_reconcile
        
        # Determine exchange direction (positive = gain/credit, negative = loss/debit)
        exchange_debit = exchange_line_vals.get('debit', 0)
        exchange_credit = exchange_line_vals.get('credit', 0)
        is_gain = exchange_credit > exchange_debit
        
        # Get total exchange amount (always positive)
        total_exchange = exchange_credit if is_gain else exchange_debit
        exchange_amount_currency = abs(exchange_line_vals.get('amount_currency', 0))
        
        # Calculate total expected tax for proportional distribution
        total_expected_tax = sum(
            abs(tax_data['expected_amount_currency'])
            for tax_data in all_tax_adjustments.values()
        )
        
        # Track remaining exchange amount to distribute
        remaining_exchange = total_exchange
        remaining_exchange_currency = exchange_amount_currency
        
        # Track total tax amounts for exchange line update
        total_tax_amount = 0.0
        total_tax_amount_currency = 0.0
        
        # Calculate tax portion from exchange amount proportionally
        tax_adjustments_list = list(all_tax_adjustments.items())
        
        for idx, (tax_key, tax_data) in enumerate(tax_adjustments_list):
            tax_repartition_line = tax_data['tax_repartition_line']
            tax_id = tax_repartition_line.tax_id
            
            # Calculate this tax's proportion based on expected tax
            if total_expected_tax:
                tax_proportion = (
                    abs(tax_data['expected_amount_currency']) /
                    total_expected_tax
                )
            else:
                # Fallback: equal distribution if no expected tax
                tax_proportion = 1.0 / len(tax_adjustments_list)
            
            # Get tax rate (e.g., 16%)
            tax_rate = tax_id.amount / 100.0
            tax_factor = 1 + tax_rate
            
            # For last tax, use remaining amount to avoid rounding issues
            if idx == len(tax_adjustments_list) - 1:
                tax_share_exchange = remaining_exchange
                tax_share_exchange_currency = remaining_exchange_currency
            else:
                # Calculate this tax's share of exchange difference
                tax_share_exchange = self.company_id.currency_id.round(
                    total_exchange * tax_proportion
                )
                tax_share_exchange_currency = tax_data['currency'].round(
                    exchange_amount_currency * tax_proportion
                )
            
            # Split this tax's share: total = base + tax
            # Formula from documentation:
            # Base = total / (1 + tax_rate) = total / 1.16
            # Tax = total - base
            # Example: 15.08 / 1.16 = 13 (base), 15.08 - 13 = 2.08 (tax)
            base_amount = self.company_id.currency_id.round(
                tax_share_exchange / tax_factor
            )
            tax_amount = tax_share_exchange - base_amount
            
            # Calculate currency amounts with same formula
            base_amount_currency = tax_data['currency'].round(
                tax_share_exchange_currency / tax_factor
            )
            tax_amount_currency = (
                tax_share_exchange_currency - base_amount_currency
            )
            
            # Update remaining amounts
            remaining_exchange -= tax_share_exchange
            remaining_exchange_currency -= tax_share_exchange_currency
            
            # Skip if tax portion is zero
            if self.company_id.currency_id.is_zero(tax_amount):
                continue
            
            # Accumulate total tax amounts for exchange line update
            total_tax_amount += tax_amount
            total_tax_amount_currency += tax_amount_currency
            
            # Get accounts based on debit/credit side (like CABA entry)
            if is_gain:
                # CREDIT side: use final tax account
                account_tax_exchange = tax_repartition_line.account_id
                if tax_id and tax_id.use_cash_basis_trans_account:
                    account_tax_exchange = tax_id.cash_basis_transition_account_id
                tax_account = account_tax_exchange
                tax_line_debit = 0.0
                tax_line_credit = tax_amount
                tax_line_amount_currency = -tax_amount_currency
            else:
                # DEBIT side: use transition account
                tax_account = tax_id.cash_basis_transition_account_id
                tax_line_debit = tax_amount
                tax_line_credit = 0.0
                tax_line_amount_currency = tax_amount_currency
            
            # Validate tax account exists
            if not tax_account:
                continue
            
            # Create ONE tax adjustment line
            existing_line_vals_list.append(
                Command.create({
                    'name': _('Tax adjustment - Exchange difference'),
                    'debit': tax_line_debit,
                    'credit': tax_line_credit,
                    'amount_currency': tax_line_amount_currency,
                    'currency_id': tax_data['currency'].id,
                    'account_id': tax_account.id,
                    'partner_id': tax_data['partner_id'],
                    'tax_repartition_line_id': tax_repartition_line.id,
                    'tax_ids': [Command.set(tax_data['tax_ids'])],
                    'tax_tag_ids': [Command.set(tax_data['tax_tag_ids'])],
                    'sequence': next_sequence,
                })
            )
            
            next_sequence += 1
        
        # Update exchange line to reflect only base amount
        # Base amount = Total exchange - All tax portions
        total_base_exchange = total_exchange - total_tax_amount
        total_base_exchange_currency = (
            exchange_amount_currency - total_tax_amount_currency
        )
        
        if is_gain:
            exchange_line_vals['credit'] = total_base_exchange
            exchange_line_vals['amount_currency'] = total_base_exchange_currency
        else:
            exchange_line_vals['debit'] = total_base_exchange
            exchange_line_vals['amount_currency'] = (
                -total_base_exchange_currency
            )

        return caba_lines_to_reconcile
    
    def _is_negative_exchange_scenario(self, exchange_move):
        """
        Detect if this exchange move is from an OVERPAYMENT scenario.
        
        Overpayment characteristics:
        - Payment amount > Invoice amount
        - Results in negative residual on invoice
        - Or payment line has credit > invoice debit
        
        :param exchange_move: account.move record (exchange entry)
        :return: Boolean - True if overpayment scenario
        """
        # Get lines that will be reconciled with this exchange move
        # These are the original invoice/payment lines
        reconciled_lines = self.env['account.move.line']
        
        # Get all lines involved in reconciliation from this exchange move
        for line in exchange_move.line_ids:
            if line.account_id.reconcile:
                # Get matched debit/credit from THIS line's future reconciliation
                # But at this point they're not reconciled yet!
                # We need to trace back to the ORIGINAL lines that TRIGGERED this exchange
                pass
        
        # Alternative: Check from self (the lines that called this method)
        for line in self:
            move = line.move_id
            
            # Check if this is an invoice line
            if not move.is_invoice(include_receipts=True):
                continue
            
            # Get all partials (payments) for this invoice line
            all_partials = (line.matched_debit_ids + line.matched_credit_ids)
            
            if not all_partials:
                continue
            
            # Calculate total paid vs invoice amount
            invoice_amount = abs(move.amount_total_signed)
            total_paid = 0.0
            
            for partial in all_partials:
                # Determine payment amount
                if partial.debit_move_id.move_id == move:
                    # Invoice is debit side
                    payment_line = partial.credit_move_id
                else:
                    # Invoice is credit side
                    payment_line = partial.debit_move_id
                
                # Accumulate paid amount in invoice currency
                total_paid += abs(payment_line.amount_currency)
            
            # Check for overpayment
            if total_paid > invoice_amount:
                # OVERPAYMENT DETECTED!
                return True
            
            # Alternative check: negative residual
            if move.amount_residual < 0:
                return True
        
        return False
    
    def _handle_negative_exchange_tax_split(self, exchange_move):
        """
        Handle tax split for NEGATIVE exchange scenario (overpayment).
        
        At this point:
        - exchange_move is created (has ID and lines)
        - exchange_move is NOT posted yet (state = 'draft')
        - We can modify/add/delete lines freely
        
        :param exchange_move: account.move record (exchange entry in draft)
        """
        # Check if we should apply tax fix
        if not self._should_apply_pao_exchange_rate_tax_fix():
            return
        
        # Get payment rates
        payment_rates_map = self._get_payment_rates_by_invoice()
        
        # Collect ALL tax adjustments from ALL moves
        all_tax_adjustments = {}
        
        for move in self.move_id:
            move_values = move._collect_tax_cash_basis_values()

            if not move_values or not move_values['is_fully_paid']:
                continue

            # STEP 1: Collect EXPECTED tax from INVOICE
            for line in move.line_ids:
                # Only process tax lines with on_payment exigibility
                if (line.tax_line_id and 
                    line.tax_line_id.tax_exigibility == 'on_payment' and
                    line.tax_repartition_line_id):
                    
                    # Get the FINAL tax account (where tax should go)
                    tax_account = (
                        line.tax_repartition_line_id.account_id
                    )
                    
                    if not tax_account:
                        continue
                    
                    tax_key = (
                        line.tax_repartition_line_id.id,
                        tax_account.id,
                    )

                    if tax_key not in all_tax_adjustments:
                        all_tax_adjustments[tax_key] = {
                            'expected_amount_currency': 0.0,
                            'tax_repartition_line': (
                                line.tax_repartition_line_id
                            ),
                            'tax_account': tax_account,
                            'currency': line.currency_id,
                            'partner_id': line.partner_id.id,
                            'tax_ids': line.tax_ids.ids,
                            'tax_tag_ids': line.tax_tag_ids.ids,
                        }

                    # Accumulate expected tax amount from invoice
                    tax_amount_on_invoice = line.balance
                    all_tax_adjustments[tax_key][
                        'expected_amount_currency'
                    ] += tax_amount_on_invoice
        
        # Skip if no tax adjustments needed
        if not all_tax_adjustments:
            return
        
        # STEP 2: Find exchange account line in the move
        exchange_accounts = [
            self.company_id.income_currency_exchange_account_id.id,
            self.company_id.expense_currency_exchange_account_id.id
        ]
        
        exchange_line = None
        for line in exchange_move.line_ids:
            if (line.account_id.id in exchange_accounts and
                not line.full_reconcile_id):
                exchange_line = line
                break
        
        # Skip if no exchange line found
        if not exchange_line:
            return
        
        # STEP 3: Determine exchange direction and amount
        is_gain = exchange_line.credit > exchange_line.debit
        total_exchange = exchange_line.credit if is_gain else exchange_line.debit
        exchange_amount_currency = abs(exchange_line.amount_currency)
        
        # Skip if zero exchange
        if self.company_id.currency_id.is_zero(total_exchange):
            return
        
        # STEP 4: Calculate total expected tax for proportional distribution
        total_expected_tax = sum(
            abs(tax_data['expected_amount_currency'])
            for tax_data in all_tax_adjustments.values()
        )
        
        # Track remaining exchange amount to distribute
        remaining_exchange = total_exchange
        remaining_exchange_currency = exchange_amount_currency
        
        # Track total tax amounts for exchange line update
        total_tax_amount = 0.0
        total_tax_amount_currency = 0.0
        
        # STEP 5: Create tax adjustment lines
        tax_adjustments_list = list(all_tax_adjustments.items())
        new_lines_vals = []
        
        for idx, (tax_key, tax_data) in enumerate(tax_adjustments_list):
            tax_repartition_line = tax_data['tax_repartition_line']
            tax_id = tax_repartition_line.tax_id
            
            # Calculate this tax's proportion based on expected tax
            if total_expected_tax:
                tax_proportion = (
                    abs(tax_data['expected_amount_currency']) /
                    total_expected_tax
                )
            else:
                # Fallback: equal distribution if no expected tax
                tax_proportion = 1.0 / len(tax_adjustments_list)
            
            # Get tax rate (e.g., 16%)
            tax_rate = tax_id.amount / 100.0
            tax_factor = 1 + tax_rate
            
            # For last tax, use remaining amount to avoid rounding issues
            if idx == len(tax_adjustments_list) - 1:
                tax_share_exchange = remaining_exchange
                tax_share_exchange_currency = remaining_exchange_currency
            else:
                # Calculate this tax's share of exchange difference
                tax_share_exchange = self.company_id.currency_id.round(
                    total_exchange * tax_proportion
                )
                tax_share_exchange_currency = tax_data['currency'].round(
                    exchange_amount_currency * tax_proportion
                )
            
            # Split this tax's share: total = base + tax
            # Formula: Base = total / (1 + tax_rate)
            base_amount = self.company_id.currency_id.round(
                tax_share_exchange / tax_factor
            )
            tax_amount = tax_share_exchange - base_amount
            
            # Calculate currency amounts with same formula
            base_amount_currency = tax_data['currency'].round(
                tax_share_exchange_currency / tax_factor
            )
            tax_amount_currency = (
                tax_share_exchange_currency - base_amount_currency
            )
            
            # Update remaining amounts
            remaining_exchange -= tax_share_exchange
            remaining_exchange_currency -= tax_share_exchange_currency
            
            # Skip if tax portion is zero
            if self.company_id.currency_id.is_zero(tax_amount):
                continue
            
            # Accumulate total tax amounts for exchange line update
            total_tax_amount += tax_amount
            total_tax_amount_currency += tax_amount_currency
            
            # Get accounts based on debit/credit side (like CABA entry)
            if is_gain:
                # CREDIT side: use final tax account
                tax_account = tax_repartition_line.account_id
                tax_line_debit = 0.0
                tax_line_credit = tax_amount
                tax_line_amount_currency = -tax_amount_currency
            else:
                # DEBIT side: use transition account
                tax_account = tax_id.cash_basis_transition_account_id
                tax_line_debit = tax_amount
                tax_line_credit = 0.0
                tax_line_amount_currency = tax_amount_currency
            
            # Validate tax account exists
            if not tax_account:
                continue
            
            # Prepare vals for new tax adjustment line
            new_lines_vals.append({
                'move_id': exchange_move.id,
                'name': _('Tax adjustment - Exchange difference'),
                'debit': tax_line_debit,
                'credit': tax_line_credit,
                'amount_currency': tax_line_amount_currency,
                'currency_id': tax_data['currency'].id,
                'account_id': tax_account.id,
                'partner_id': tax_data['partner_id'],
                'tax_repartition_line_id': tax_repartition_line.id,
                'tax_ids': [Command.set(tax_data['tax_ids'])],
                'tax_tag_ids': [Command.set(tax_data['tax_tag_ids'])],
            })
        
        # STEP 6: Create new tax lines
        if new_lines_vals:
            self.env['account.move.line'].create(new_lines_vals)
        
        # STEP 7: Update exchange line to reflect only base amount
        # Base amount = Total exchange - All tax portions
        total_base_exchange = total_exchange - total_tax_amount
        total_base_exchange_currency = (
            exchange_amount_currency - total_tax_amount_currency
        )
        
        if is_gain:
            exchange_line.write({
                'credit': total_base_exchange,
                'amount_currency': -total_base_exchange_currency,
            })
        else:
            exchange_line.write({
                'debit': total_base_exchange,
                'amount_currency': total_base_exchange_currency,
            })
