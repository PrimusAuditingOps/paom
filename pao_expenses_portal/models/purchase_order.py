from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PurchaseOrderReportInherit(models.Model):

    _inherit="purchase.order"
    
    sheet_id = fields.Many2one('hr.expense.sheet', string='Expense Report', default=None)