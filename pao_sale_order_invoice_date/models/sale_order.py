from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit="sale.order"

    pao_invoice_date = fields.Date(compute="_compute_invoice", string="Invoice Date", store=True)
            
    @api.depends('invoice_ids.invoice_date')
    def _compute_invoice(self):
        for order in self:
            first_invoice = None
            for invoice in order.invoice_ids.filtered_domain([('state', '=', 'posted')]):
                    if not first_invoice or invoice.invoice_date < first_invoice:
                        first_invoice = invoice.invoice_date
            order.pao_invoice_date = first_invoice
