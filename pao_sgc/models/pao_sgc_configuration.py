from odoo import models, fields, tools, api

class PaoSGCDepartment(models.Model):

    _name="pao.sgc.department"
    _description = "Catalog of departments used in SGC moduel"
    
    name = fields.Char('Name', translate=True, required=True)
    internal_name = fields.Char('Internal Name')
    
    @api.model 
    def create(self, values):
        record = super(PaoSGCDepartment, self).create(values)
        
        if not record.internal_name:
            internal_name = record.name.lower().replace(" ", "_")
            record.internal_name = internal_name
            
        return record

class PaoSGCScheme(models.Model):

    _name="pao.sgc.scheme"
    _description = "Catalog of schemes used in SGC moduel"
    
    name = fields.Char('Name', translate=True, required=True)
    internal_name = fields.Char('Internal Name')
    
    @api.model 
    def create(self, values):
        record = super(PaoSGCScheme, self).create(values)
        
        if not record.internal_name:
            internal_name = record.name.lower().replace(" ", "_")
            record.internal_name = internal_name
            
        return record 

