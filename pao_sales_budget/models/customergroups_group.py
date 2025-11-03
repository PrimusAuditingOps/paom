from odoo import fields, models, api

class CustomergroupsGroup(models.Model):
    _inherit = 'customergroups.group'

    pao_include_in_budget = fields.Boolean(string='Include in Budget',default=False)