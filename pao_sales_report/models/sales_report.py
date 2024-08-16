from odoo import models, fields, api

class SaleReportInherit(models.Model):
    _inherit="sale.report"

    ship_date = fields.Date('Ship Date', readonly=True, default=None)
    organization_id = fields.Many2one('servicereferralagreement.organization', 'Organization', readonly=True, default=None)
    registry_number_id = fields.Many2one('servicereferralagreement.registrynumber', 'Registry Number', readonly=True, default=None)
    audit_date = fields.Date('Audit Date', readonly=True, default=None)
    end_date = fields.Date('End Date', readonly=True, default=None)
    
    def _group_by_sale(self):
        group_by_fields = super(SaleReportInherit, self)._group_by_sale()
        
        group_by_fields += """
            ,s.date_order
            ,l.organization_id
            ,l.registrynumber_id
            ,l.service_start_date
            ,l.service_end_date
        """
        
        return group_by_fields
    
    
    def _select_sale(self):
        select_fields = super(SaleReportInherit, self)._select_sale()
        
        select_fields += """
            ,COALESCE(s.date_order, NULL) as ship_date
            ,COALESCE(l.service_start_date, NULL) as audit_date
            ,COALESCE(l.registrynumber_id, NULL) as registry_number_id
            ,COALESCE(l.organization_id, NULL) as organization_id
            ,COALESCE(l.service_end_date, NULL) as end_date
        """
        
        return select_fields
    