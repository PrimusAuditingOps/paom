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
    
    # pao_requirement = fields.Selection(
    #     selection=[
    #         ('0', "Electronic signatures / Business cards."),
    #         ('1', "Upload documents to the website."),
    #         ('2', "Memos for satellite offices."),
    #         ('3', "Updates to existing designs"),
    #         ('4', "New designs (banners, flyers, etc.)"),
    #         ('5', "Souvenir orders - USA"),
    #         ('9', "Other"),
    #     ],
    #     string="Requirement",
    #     tracking=True,
    # )
    