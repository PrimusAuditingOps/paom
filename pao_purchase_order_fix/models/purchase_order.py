from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    @api.depends(
        'order_line.invoice_lines.move_id',
        'order_line.invoice_lines.move_id.state',
    )
    def _compute_invoice(self):
        for order in self:
            invoices = order.mapped('order_line.invoice_lines.move_id')
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)
        