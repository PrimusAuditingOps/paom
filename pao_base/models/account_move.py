from odoo import api, models, fields
from odoo.tools.translate import _


class ResPartner(models.Model):
    _inherit = 'account.move'

    audit_date = fields.Date(string="Audit Date", compute="_get_audit_date", store=True)
    organization = fields.Char(string="Organization", compute="_get_organization", store=True)
    registry_number = fields.Char(string="Registry Number", compute="_get_registry_number", store=True)
    
    @api.depends('line_ids.sale_line_ids.order_id')
    def _get_audit_date(self):
        source_orders = self.line_ids.sale_line_ids.order_id
        
        self.audit_date = None
        if source_orders:
            self.audit_date = source_orders[0].service_start_date
    
    @api.depends('line_ids.sale_line_ids.order_id')
    def _get_organization(self):
        source_orders = self.line_ids.sale_line_ids.order_id
        
        self.organization = None
        if source_orders:
            organization = source_orders[0].organization_id
            self.organization = organization.name if organization else None
            
    @api.depends('line_ids.sale_line_ids.order_id')
    def _get_registry_number(self):
        source_orders = self.line_ids.sale_line_ids.order_id
        
        self.registry_number = None
        if source_orders:
            registry_number = source_orders[0].registrynumber_id
            self.registry_number = registry_number.name if registry_number else None