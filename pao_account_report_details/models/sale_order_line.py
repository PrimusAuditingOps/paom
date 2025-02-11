from odoo import fields, models, api

class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order'
    
    audit_date = fields.Date(compute="_compute_audit_date", string="Audit Date")
    
    @api.depends('order_line.audit_date')
    def _compute_audit_date(self):
        for rec in self:
            rec.audit_date = None
            sale_line_with_audit_date = rec.order_line.filtered('audit_date')
            if sale_line_with_audit_date:
                rec.audit_date = sale_line_with_audit_date[0].audit_date
    
class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    
    audit_date = fields.Date(
        string="Audit Date"
    )
    
    @api.onchange('service_start_date', 'service_end_date')
    def _onchange_service_dates(self):
        for record in self:
            if record.order_id.company_id.country_code == 'US' and record.service_start_date and record.service_end_date and record.service_start_date == record.service_end_date:
                record.audit_date = record.service_start_date