# PAO: Exchange Rate Tax Adjustment

## Overview

This module fixes the incorrect allocation of tax amounts when exchange rate journal entries are created for invoices with cash basis taxes (tax exigibility = "Based on Payment").

## Problem Description

In standard Odoo 17, when:
1. An invoice is created with foreign currency and tax exigibility set to "Based on Payment"
2. Payment is made on a different date (or in different currency) triggering exchange rate differences
3. The invoice becomes fully paid

The tax amounts are incorrectly split between:
- Tax account (incomplete amount)
- Exchange gain/loss account (contains portion of tax that should be in tax account)

### Example

**Invoice** (17 Sept 2025, USD):
- Product: $923.79
- Tax 16%: $147.81
- Total: $1,071.60

**Payment** (20 Sept 2025, MXN):
- Exchange rate difference triggered
- Expected tax in tax account: $147.81
- **Actual result in standard Odoo:**
  - Tax account: $146.89 ❌
  - Exchange account: includes $0.92 of tax ❌

## Root Cause

In `account_move_line.py`, method `_add_exchange_difference_cash_basis_vals` (line 2934-2937):

```python
# Standard Odoo code uses rate from LAST cash basis move
last_caba_move = max(cash_basis_moves, key=lambda m: m.date)
currency_line = last_caba_move.line_ids.filtered(lambda x: x.currency_id == currency)[:1]
currency_rate = currency_line.balance / currency_line.amount_currency
```

This `currency_rate` may differ from the `payment_rate` used when creating cash basis entries, causing tax adjustments to be calculated incorrectly.

## Solution

This module overrides `_add_exchange_difference_cash_basis_vals` to:
1. Calculate actual `payment_rate` from partial reconcile records
2. Use this consistent rate for tax adjustment calculations
3. Ensure tax amounts go 100% to tax accounts

The fix uses weighted average payment rate across all payments to ensure accuracy even with multiple partial payments.

## Preconditions

The module's logic is ONLY applied when:
1. ✅ Payment triggers exchange rate journal entry creation
2. ✅ Tax exigibility is "Based on Payment" (on_payment)
3. ✅ There are exchange rate differences
4. ✅ Invoice is fully paid

If these conditions are not met, standard Odoo behavior is used (no side effects).

## Technical Details

### Modified Method

**File**: `models/account_move_line.py`
**Method**: `_add_exchange_difference_cash_basis_vals`

**Strategy**:
1. Check if preconditions are met via `_should_apply_pao_exchange_rate_tax_fix()`
2. If not met → use super() (standard Odoo behavior)
3. If met → calculate payment rates via `_get_payment_rates_by_invoice()`
4. Apply proper rate calculation via `_pao_add_exchange_diff_cash_basis_with_proper_rate()`

### Key Changes

**Line 337 in our implementation** (equivalent to standard Odoo line 2937):
```python
# OLD (Standard Odoo):
currency_rate = currency_line.balance / currency_line.amount_currency

# NEW (This Module):
currency_rate = payment_rates_map.get(move.id, 1.0)
```

This ensures the same rate used in cash basis entry creation is used for tax adjustments.

## Testing

### Test Scenario

1. Create customer invoice:
   - Date: any date
   - Currency: USD (or any foreign currency)
   - Product line with amount
   - Tax with 16% rate and "Based on Payment" exigibility

2. Post the invoice

3. Register payment:
   - Date: different from invoice date (to trigger exchange difference)
   - Currency: MXN (or different from invoice)
   - Amount: full payment

4. Check cash basis entries:
   - Tax account should have FULL tax amount
   - Exchange gain/loss account should NOT contain any tax amounts

### Expected Result

With this module:
- ✅ Tax account receives 100% of tax amount
- ✅ Exchange differences are recorded in exchange gain/loss accounts
- ✅ Tax amounts are NOT mixed with exchange differences

## Installation

1. Copy module to addons directory
2. Update apps list
3. Install "PAO: Exchange Rate Tax Adjustment"

## Dependencies

- `account` (Odoo core accounting module)

## Compatibility

- **Odoo Version**: 17.0
- **Database**: PostgreSQL
- **Python**: 3.10+

## Author

Port Cities  
https://www.portcities.net

## License

LGPL-3

## Version History

### 1.0.0 (2025-10-07)
- Initial release
- Fixes tax allocation in exchange rate journal entries
- Supports multiple partial payments with weighted average rate calculation
- Full backward compatibility with standard Odoo behavior when preconditions not met
