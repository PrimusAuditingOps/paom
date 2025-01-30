from odoo import fields, models, api

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    
    audit_dates_available = fields.Boolean(compute="_compute_audit_dates_available", store=True)

    @api.depends('invoice_line_ids.sale_line_ids.order_id', 
                'invoice_line_ids.sale_line_ids.order_id.service_end_date', 
                'invoice_line_ids.sale_line_ids.service_end_date')
    def _compute_audit_dates_available(self):
        for move in self:
            # Get the related sale orders from the invoice lines
            sale_orders = move.invoice_line_ids.sale_line_ids.order_id

            # Initialize the flag as False
            move.audit_dates_available = False

            # Check if any sale order has service_end_date set
            if sale_orders and any(so.service_end_date for so in sale_orders):
                move.audit_dates_available = True
            else:
                # Check if any sale order line has service_end_date set
                sale_lines = move.invoice_line_ids.sale_line_ids
                if sale_lines and any(line.service_end_date for line in sale_lines):
                    move.audit_dates_available = True