from odoo import models, fields, api

class SaleReportInherit(models.Model):
    _inherit="sale.report"

    ship_date = fields.Date('Ship Date', readonly=True)
    organization_id = fields.Many2one('servicereferralagreement.organization', 'Organization', readonly=True)
    registry_number_id = fields.Many2one('servicereferralagreement.registrynumber', 'Registry Number', readonly=True)
    audit_date = fields.Date('Audit Date', readonly=True)
    end_date = fields.Date('End Date', readonly=True)
    
    def _select_sale(self):
        select_fields = super(SaleReportInherit, self)._select_sale()
        
        select_fields += """, 
            s.date_order as ship_date,
            l.service_start_date as audit_date,
            l.registrynumber_id as registry_number_id,
            -- l.organization_id as organization_id, 
            l.service_end_date as end_date
        """
        
        return select_fields
    
    def _group_by_sale(self):
        group_by_fields = super(SaleReportInherit, self)._group_by_sale()
        
        group_by_fields += """, 
            s.date_order
            l.organization_id
            l.registrynumber_id
            l.service_start_date
            l.service_end_date
        """
        
        return group_by_fields