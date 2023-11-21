from odoo import models, fields, api

class PurchaseReportInherit(models.Model):
    _inherit = "purchase.report"

    pao_invoice_date = fields.Date(string="Invoice Date")
    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
    ], string='Billing Status', default='no')
    
    def _select(self):
        return super(PurchaseReportInherit, self)._select() + ", po.pao_invoice_date as pao_invoice_date, po.invoice_status as invoice_status"

    def _group_by(self):
        return super(PurchaseReportInherit, self)._group_by() + ", po.pao_invoice_date, po.invoice_status"

