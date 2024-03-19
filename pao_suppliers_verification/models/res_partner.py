from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class ResPartnerInherit(models.Model):
    _inherit = "res.partner"
    
    affects_certification_process = fields.Boolean('Affects the certification process', default=False)
    service_type_id = fields.Many2one('pao.supplier.service', string="Service Type")
    branch_office_ids = fields.Many2many(
        string='Branch Office',
        comodel_name='pao.supplier.branch.office'
    )
    
    
class SupplierService(models.Model):
    _name = "pao.supplier.service"
    
    name = fields.Char('Name', translate=True, required=True)
    internal_name = fields.Char('Internal Name')
    
    @api.model 
    def create(self, values):
        record = super(SupplierService, self).create(values)
        
        if not record.internal_name:
            internal_name = record.name.lower().replace(" ", "_")
            record.internal_name = internal_name
            
        return record
    

class SupplierBranchOffice(models.Model):
    _name = "pao.supplier.branch.office"
    
    name = fields.Char('Name', required=True)
