from odoo import fields, models, api

class CRMTeam(models.Model):
    _inherit = 'crm.team'

    pao_include_in_budget = fields.Boolean(string='Include in Budget',default=False)