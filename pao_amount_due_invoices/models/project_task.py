from odoo import models, fields, api, _

class ProjectTask(models.Model):

    _inherit='project.task'

    pao_total_due = fields.Monetary(
        string="Total Due",
        currency_field='currency_id',
        default=0.00,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id or False,
        readonly=True,
    )