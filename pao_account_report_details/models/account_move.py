from odoo import fields, models, api

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    
    audit_dates_available = fields.Boolean(compute="_compute_audit_dates_available", store=True)
    
    audit_date = fields.Date(compute="_compute_audit_date", string="Audit Date")

    @api.depends('invoice_line_ids.sale_line_ids.order_id', 
                'invoice_line_ids.sale_line_ids.audit_date')
    def _compute_audit_dates_available(self):
        for move in self:
            move.audit_dates_available = False

            sale_lines = move.invoice_line_ids.sale_line_ids
            if sale_lines and any(line.audit_date for line in sale_lines):
                move.audit_dates_available = True
                
    @api.depends('invoice_line_ids.sale_line_ids.order_id', 
                'invoice_line_ids.sale_line_ids.audit_date')
    def _compute_audit_date(self):
        for move in self:
            move.audit_date = None
            sale_line_with_audit_date = move.invoice_line_ids.sale_line_ids.filtered('audit_date')
            if sale_line_with_audit_date:
                move.audit_date = sale_line_with_audit_date[0].audit_date
