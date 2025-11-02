from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PurchaseOrderReportInherit(models.Model):

    _inherit="purchase.order"
    
    sheet_id = fields.Many2one('hr.expense.sheet', string='Expense Report', default=None) # NOT IN USE
    
    expense_sheet_ids = fields.One2many(
        'hr.expense.sheet',
        'purchase_order',
        string='Expense Reports'
    )
