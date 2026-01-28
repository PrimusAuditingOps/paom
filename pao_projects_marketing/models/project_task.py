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
    
    pao_requirement = fields.Selection(
        selection=[
            ('0', "Electronic signatures / Business cards."),
            ('1', "Upload documents to the website."),
            ('2', "Memos for satellite offices."),
            ('3', "Updates to existing designs"),
            ('4', "New designs (banners, flyers, etc.)"),
            ('5', "Souvenir orders - USA"),
        ],
        string="Requirement",
        tracking=True,
    )
    
    @api.onchange('pao_requirement')
    def _onchange_pao_requirement(self):
        if not self.pao_requirement:
            return

        descriptions = dict(self._fields['pao_requirement'].selection)

        self.description = descriptions.get(self.pao_requirement, '')
    
    