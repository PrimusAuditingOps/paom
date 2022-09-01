from odoo import fields, models
class PaaAsignmentAuditorScheme(models.Model):
    _name='paa.assignment.auditor.scheme'
    _description = 'Schemes'
    
    name = fields.Char(
        string="Scheme",
        requiered=True,
    )