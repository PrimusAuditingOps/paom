from odoo import models, fields, api, _

class ProjectTask(models.Model):

    _inherit='project.task'
    
    pao_responsible = fields.Selection(
        selection=[
            ('US', "MKT USA"),
            ('MX', "MKT MX"),
            ('CR', "MKT CR"),
            ('CL', "MKT CL"),
        ],
        string="Responsible",
        tracking=True,
    )
    
    pao_requirement_id = fields.Many2one(
        comodel_name='pao.requirement.types.project',
        string='Requirement',
        tracking=True,
    )
    