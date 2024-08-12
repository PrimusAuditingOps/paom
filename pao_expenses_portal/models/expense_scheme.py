from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ExpenseScheme(models.Model):
    _name = 'expense.scheme'
    
    name = fields.Char(string="Name", required=True)
    internal_reference = fields.Char(string="Internal Reference")
    property_account_expense_id = fields.Many2one('account.account', company_dependent=True, required=True,
        string="Expense Account",
        domain="[('deprecated', '=', False), ('account_type', 'not in', ('asset_receivable','liability_payable','asset_cash','liability_credit_card','off_balance')), ('company_id', '=', company_id)]",
        help="Keep this field empty to use the default value from the product category. If anglo-saxon accounting with automated valuation method is configured, the expense account on the product category will be used.")
    
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    
    
    @api.model 
    def create(self, values):
        record = super(ExpenseScheme, self).create(values)
        
        if not record.internal_reference:
            internal_reference = record.name.lower().replace(" ", "_")
            record.internal_reference = internal_reference
            
        return record 
