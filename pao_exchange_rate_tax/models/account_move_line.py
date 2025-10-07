# -*- coding: utf-8 -*-
from odoo import api, models, Command, _
from collections import defaultdict


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.model
    def _create_exchange_difference_moves(self, exchange_diff_values_list):
        """
        OVERRIDE to add tax adjustment lines to exchange entries
        BEFORE they are created.
        
        This handles BOTH:
        - Partial exchange (created during payment)
        - Full exchange (created when fully reconciled)
        """
        # Process each exchange_diff_values and add tax adjustment lines
        for exchange_diff_values in exchange_diff_values_list:
            self._add_tax_adjustment_to_exchange_vals(exchange_diff_values)
        
        # Call super to create the moves with modified values
        return super()._create_exchange_difference_moves(exchange_diff_values_list)
    
    def _add_tax_adjustment_to_exchange_vals(self, exchange_diff_vals):
        """
        Add tax adjustment lines to exchange_diff_vals['move_values']['line_ids']
        if there are cash basis taxes that need adjustment.
        """
        # Get lines from to_reconcile
        if not exchange_diff_vals.get('to_reconcile'):
            return
        
        # Check if exchange lines have actual amounts
        # Skip if all exchange lines are zero (no actual exchange difference)
        move_vals = exchange_diff_vals.get('move_values', {})
        line_ids = move_vals.get('line_ids', [])
        
        has_exchange_amount = True
        for line_cmd in line_ids:
            if line_cmd[0] == 0:  # Command.create
                line_vals = line_cmd[2]
                debit = line_vals.get('debit', 0)
                credit = line_vals.get('credit', 0)
                if debit != 0 and credit != 0:
                    has_exchange_amount = False
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
        lines._pao_add_exchange_diff_cash_basis_with_proper_rate(
            exchange_diff_vals,
            payment_rates_map
        )

    def _add_exchange_difference_cash_basis_vals(self, exchange_diff_vals):
        """
        OVERRIDE to prevent base Odoo from adding tax lines here,
        because we handle it in _create_exchange_difference_moves instead.
        
        This prevents DUPLICATE tax lines for FULL exchange entries.
        
        We still need to return caba_lines_to_reconcile for base reconciliation logic.
        """
        # Check if we should handle this with our custom logic
        if not self._should_apply_pao_exchange_rate_tax_fix():
            # Use base logic for non-custom cases
            return super()._add_exchange_difference_cash_basis_vals(exchange_diff_vals)
        
        # For our custom cases, we DON'T add lines here
        # (they will be added in _create_exchange_difference_moves)
        # But we still need to collect caba_lines_to_reconcile for reconciliation
        
        caba_lines_to_reconcile = defaultdict(lambda: self.env['account.move.line'])
        
        for move in self.move_id:
            move_values = move._collect_tax_cash_basis_values()
            if not move_values or not move_values['is_fully_paid']:
                continue
            
            # Collect CABA lines for reconciliation (from base logic)
            cash_basis_moves = self.env['account.move'].search([
                ('tax_cash_basis_origin_move_id', '=', move.id)
            ])
            
            caba_transition_accounts = self.env['account.account']
            for line in cash_basis_moves.line_ids:
                if line.tax_repartition_line_id:
                    transition_account = line.tax_line_id.cash_basis_transition_account_id
                    caba_transition_accounts |= transition_account
                    if line.account_id.reconcile:
                        caba_lines_to_reconcile[(move, line.account_id, line.tax_repartition_line_id)] |= line
            
            # Collect the caba lines affecting the transition account
            for transition_line in filter(lambda x: x.account_id in caba_transition_accounts, cash_basis_moves.line_ids):
                caba_reconcile_key = (transition_line.move_id, transition_line.account_id, transition_line.tax_repartition_line_id)
                caba_lines_to_reconcile[caba_reconcile_key] |= transition_line
        
        return caba_lines_to_reconcile
    
    def _should_apply_pao_exchange_rate_tax_fix(self):
        """
        Check if the custom tax fix should be applied.
        
        Returns True if:
        1. There are invoices with cash basis taxes involved
        2. Company has tax exigibility enabled
        3. There are partial reconcile records (payments made)
        """
        # Check if any of the moves have cash basis taxes
        for move in self.move_id:
            if not move.is_invoice(include_receipts=True):
                continue
                
            move_values = move._collect_tax_cash_basis_values()
            if move_values and move_values.get('to_process_lines'):
                # Check if there are tax lines with on_payment exigibility
                has_cash_basis_tax = any(
                    caba_treatment == 'tax' and line.tax_line_id.tax_exigibility == 'on_payment'
                    for caba_treatment, line in move_values['to_process_lines']
                )
                if has_cash_basis_tax:
                    # Verify there are partials (payments)
                    partials = self.matched_debit_ids + self.matched_credit_ids
                    if partials:
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

    def _pao_add_exchange_diff_cash_basis_with_proper_rate(
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

            currency = move_values['currency']
            move_vals['date'] = max(move_vals['date'], move.date)

            # STEP 1: Collect EXPECTED tax from INVOICE LINES directly
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
                            'caba_amount_currency': 0.0,
                            'tax_repartition_line': (
                                line.tax_repartition_line_id
                            ),
                            'tax_account': tax_account,
                            'currency': line.currency_id,
                            'partner_id': line.partner_id.id,
                            'tax_ids': line.tax_ids.ids,
                            'tax_tag_ids': line.tax_tag_ids.ids,
                        }

                    # Accumulate expected tax amount
                    all_tax_adjustments[tax_key][
                        'expected_amount_currency'
                    ] += line.balance

            # STEP 2: Subtract ACTUAL tax from CABA entries
            cash_basis_moves = self.env['account.move'].search([
                ('tax_cash_basis_origin_move_id', '=', move.id)
            ])

            for caba_move in cash_basis_moves:
                for line in caba_move.line_ids:
                    if line.tax_repartition_line_id:
                        tax_account = (
                            line.tax_repartition_line_id.account_id
                        )
                        
                        if not tax_account:
                            continue

                        tax_key = (
                            line.tax_repartition_line_id.id,
                            tax_account.id,
                        )

                        if tax_key in all_tax_adjustments:
                            # Only count lines TO the final tax account
                            if line.account_id.id == tax_account.id:
                                all_tax_adjustments[tax_key][
                                    'caba_amount_currency'
                                ] += line.balance

            # STEP 3: Get proper payment rate
            currency_rate = payment_rates_map.get(move.id)

            if currency_rate is None:
                last_caba_move = max(
                    cash_basis_moves,
                    key=lambda m: m.date
                ) if cash_basis_moves else self.env['account.move']
                currency_line = last_caba_move.line_ids.filtered(
                    lambda x: x.currency_id == currency
                )[:1]
                if currency_line and currency_line.amount_currency:
                    currency_rate = (
                        currency_line.balance /
                        currency_line.amount_currency
                    )
                else:
                    currency_rate = 1.0

        # STEP 4: Split exchange difference proportionally between base and tax
        existing_line_vals_list = move_vals['line_ids']
        next_sequence = len(existing_line_vals_list)
        
        # Find exchange account line (the one with gain/loss account)
        exchange_line_vals = None
        exchange_line_idx = None
        
        for idx, line_cmd in enumerate(existing_line_vals_list):
            if line_cmd[0] == 0:  # Command.create
                line_vals = line_cmd[2]
                if ('Currency exchange rate difference' in line_vals.get('name', '') and
                    line_vals.get('account_id') in [
                        self.company_id.income_currency_exchange_account_id.id,
                        self.company_id.expense_currency_exchange_account_id.id
                    ]):
                    exchange_line_vals = line_vals
                    exchange_line_idx = idx
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
        
        # Calculate tax portion from exchange amount
        for tax_key, tax_data in all_tax_adjustments.items():
            tax_repartition_line = tax_data['tax_repartition_line']
            tax_id = tax_repartition_line.tax_id
            
            # Get tax rate (e.g., 16%)
            tax_rate = tax_id.amount / 100.0
            tax_factor = 1 + tax_rate
            
            # Split: total = base + tax
            # Example: 15.08 = 13.00 + 2.08 (with 16% tax)
            base_amount = self.company_id.currency_id.round(total_exchange / tax_factor)
            tax_amount = total_exchange - base_amount
            
            # Calculate currency amounts proportionally
            base_amount_currency = tax_data['currency'].round(exchange_amount_currency / tax_factor)
            tax_amount_currency = exchange_amount_currency - base_amount_currency
            
            # Skip if tax portion is zero
            if self.company_id.currency_id.is_zero(tax_amount):
                continue
            
            # Get accounts based on debit/credit side (like CABA entry)
            tax_repartition_line = tax_data['tax_repartition_line']
            tax_id = tax_repartition_line.tax_id
            
            # Reduce exchange line by tax portion
            if is_gain:
                exchange_line_vals['credit'] = base_amount
                exchange_line_vals['amount_currency'] = base_amount_currency
                
                # CREDIT side: use final tax account (208)
                tax_account = tax_repartition_line.account_id
                tax_line_debit = 0.0
                tax_line_credit = tax_amount
                tax_line_amount_currency = -tax_amount_currency
            else:
                exchange_line_vals['debit'] = base_amount
                exchange_line_vals['amount_currency'] = -base_amount_currency
                
                # DEBIT side: use transition account (209)
                tax_account = tax_id.cash_basis_transition_account_id
                tax_line_debit = tax_amount
                tax_line_credit = 0.0
                tax_line_amount_currency = tax_amount_currency
            
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

        return caba_lines_to_reconcile
