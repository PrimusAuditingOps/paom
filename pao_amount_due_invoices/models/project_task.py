from odoo import models, fields, api, _

class ProjectTask(models.Model):

    _inherit='project.task'

    pao_total_due = fields.Monetary(
        string="Total Due",
        default=0,
    )