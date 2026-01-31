from odoo import models, fields

class PAORequirementTypesProject(models.Model):
    _name = 'pao.requirement.types.project'
    _description = 'Requirement Types for Projects'
    
    name = fields.Char(string="Name", required=True,translate=True)
    
    project_id = fields.Many2many(
        comodel_name='project.project',
        string='Project',
        required=True
    )