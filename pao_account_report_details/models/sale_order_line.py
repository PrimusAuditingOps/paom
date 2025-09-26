from odoo import fields, models, api

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    
    audit_date = fields.Date(compute="_compute_audit_date", string="Audit Date", store=True)
    
    @api.depends('order_line.audit_date')
    def _compute_audit_date(self):
        for rec in self:
            rec.audit_date = None
            sale_line_with_audit_date = rec.order_line.filtered('audit_date')
            if sale_line_with_audit_date:
                rec.audit_date = sale_line_with_audit_date[0].audit_date
    
    @api.onchange('order_line')
    def _onchange_audit_date_line(self):
        if self.company_id.country_code == 'US':
            updated_lines = self.order_line.filtered(
                lambda line: line.audit_date_changed and line.audit_date and line.organization_id and line.registrynumber_id
            )
            
            if updated_lines:
                updated_line = updated_lines[0]
                for line in self.order_line:
                    if line.organization_id.id == updated_line.organization_id.id and line.registrynumber_id.id == updated_line.registrynumber_id.id:
                        line.update({'audit_date_changed': False})
                        line.update({'audit_date': updated_line.audit_date})
    
class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    
    audit_date = fields.Date(string="Audit Date")
    audit_date_changed = fields.Boolean(default=False)
    
    @api.onchange('registrynumber_id')
    def _copy_audit_date(self):
        for rec in self:
            if rec.order_id.company_id.country_code == 'US' and rec.registrynumber_id and rec.order_id:
                audit_lines = rec.order_id.order_line.filtered(
                    lambda line:    line.id != rec.id and
                                    line.audit_date and
                                    line.registrynumber_id.id == rec.registrynumber_id.id and
                                    line.organization_id.id == rec.organization_id.id
                )
                if audit_lines:
                    rec.audit_date = audit_lines[0].audit_date
                    
    @api.onchange('service_start_date', 'service_end_date')
    def _onchange_service_dates(self):
        """ Set audit_date when service_start_date and service_end_date are the same. """
        for line in self:
            if line.order_id.company_id.country_code == 'US' and line.service_start_date and line.service_end_date and line.service_start_date == line.service_end_date:
                line.audit_date = line.service_start_date
                line.audit_date_changed = True

    @api.onchange('audit_date')
    def _onchange_audit_date(self):
        """ Set service_start_date and service_end_date when audit_date is manually updated. """
        for line in self:
            if line.order_id.company_id.country_code == 'US' and line.audit_date:
                # line.service_start_date = line.audit_date
                # line.service_end_date = line.audit_date
                line.audit_date_changed = True