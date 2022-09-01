from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from logging import getLogger

_logger = getLogger(__name__)
class PaaAuditorQualification(models.Model):
    _name = 'paoassignmentauditor.auditor.qualification'
    _description = 'Auditor assignment Qualification'
    _rec_name = 'auditor_id'
    _order = 'qualification desc'




    auditor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Auditor',
        ondelete='set null',
    )
    position = fields.Integer(
        string='Position',
        compute="_get_position"
    )
    scheme_qualification = fields.Float(
        default = 0.00,
        required = True,
        string= "Scheme Qualification",
    )
    localization_qualification = fields.Float(
        default = 0.00,
        required = True,
        string= "Localization Qualification",
    )
    audit_qty_qualification = fields.Float(
        default = 0.00,
        required = True,
        string= "Audit Quantity Qualification",
    )
    audit_honorarium_qualification = fields.Float(
        default = 0.00,
        required = True,
        string= "Audit honorarium Qualification",
    )
    qualification = fields.Float(
        default = 0.00,
        required = True,
        string= "Qualification",
    )
    ref_user_id = fields.Integer(
        string='User ID',
    )
    assigned_auditor_id = fields.Integer(
        string="Assigned auditor id",
        default = 0,
    ) 
    assigned_auditor_position = fields.Integer(
        string = "Pos Reference",
        default = 0,
    ) 
    assigned_auditor_qualification = fields.Float(
        default = 0.00,
        string = "Qual Reference",
    ) 

    def _get_position(self):
        
        for rec in self:
            domain = [("ref_user_id","=",rec.ref_user_id)]
            rec_qualifications = self.env['paoassignmentauditor.auditor.qualification'].search(domain,order = 'qualification desc')
            position = 0
            for qln in rec_qualifications:
                position += 1
                if qln.auditor_id.id == rec.auditor_id.id:
                    rec.position = position
                    break

        

    def assign_auditor(self,context=None):
        for rec in self:
            rec.write({'assigned_auditor_id': rec.auditor_id.id})
            domain = [("ref_user_id","=",rec.ref_user_id)]
            rec_auditor_qualification = self.env['paoassignmentauditor.auditor.qualification'].search(domain)
            for rec_aq in rec_auditor_qualification:
                rec_aq.write({'assigned_auditor_id': rec.auditor_id.id,'assigned_auditor_position': rec.position,'assigned_auditor_qualification': rec.qualification})
        return {'type': 'ir.actions.act_window_close'}