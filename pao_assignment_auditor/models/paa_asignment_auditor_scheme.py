from odoo import fields, models



class PaaAsignmentAuditorScheme(models.Model):
    _name = 'paa.assignment.auditor.scheme'
    _description = 'Schemes'
    
    name = fields.Char(string="Scheme", required=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)