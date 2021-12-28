from datetime import datetime, timedelta
from odoo import fields, models, api
from logging import getLogger

_logger = getLogger(__name__)
class SaleOrder(models.Model):

    _inherit='sale.order'
    
    purchase_order_id = fields.One2many(
        comodel_name='purchase.order',
        inverse_name='sale_order_id',
        string='Purchase Order',
    )
    enable_organization_ids = fields.Many2many(
        related="partner_id.organization_ids",
    )
    coordinator_id = fields.Many2one(
        string="Coordinator",
        comodel_name='res.users',
        ondelete='set null',
        index=True,
        domain = [('share','=',False)],
    )
    registration_number_order_lines_ids = fields.Many2many(
        comodel_name='servicereferralagreement.registrynumber', 
        compute='_get_registration_number', 
        string='Registration number order lines',
        readonly=True,
    )   
    def _get_registration_number(self):
        rn = []
        for rec in self:
            for orderline in rec.order_line:
                if orderline.registrynumber_id.id not in rn:
                    rn.append(orderline.registrynumber_id.id)
            
            rec.registration_number_order_lines_ids = rn
    
    registration_number_print = fields.Many2one(
        string="Document to print",
        comodel_name='servicereferralagreement.registrynumber',
        ondelete='set null',
        index=True,
    )
    
    @api.onchange('coordinator_id')
    def _change_coordinator(self):
        for rec in self:
            for line in rec.order_line:
                if line.product_id:
                    line.coordinator_id = rec.coordinator_id

    @api.onchange('order_line')
    def _change_date(self):
        organization = -1
        registrynumber = -1
        service_end_date = None
        service_start_date = None
        coordinator = 0
        for rec in self.order_line.sorted(key=lambda r: (r.organization_id.id,r.registrynumber_id.id,r.update_number), reverse=True):
            if rec.product_id and rec.organization_id:        
                if not organization == rec.organization_id.id or not registrynumber == rec.registrynumber_id.id:
                    service_start_date = rec.service_start_date
                    service_end_date = rec.service_end_date
                else:
                    rec.update({'service_end_date': service_end_date})
                    rec.update({'service_start_date': service_start_date})
                organization = rec.organization_id.id
                registrynumber = rec.registrynumber_id.id
        organization = -1
        registrynumber = -1
        for rec in self.order_line.sorted(key=lambda r: (r.organization_id.id,r.registrynumber_id.id,r.update_number_coordinator), reverse=True):
            if rec.product_id and rec.organization_id:        
                if not organization == rec.organization_id.id or not registrynumber == rec.registrynumber_id.id:
                    coordinator = rec.coordinator_id.id
                else:
                    rec.update({'coordinator_id': coordinator})
                organization = rec.organization_id.id
                registrynumber = rec.registrynumber_id.id
    
    