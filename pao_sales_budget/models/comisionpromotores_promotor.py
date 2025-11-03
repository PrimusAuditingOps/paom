from odoo import fields, models, api

class ComisionpromotoresPromotor(models.Model):
    _inherit = 'comisionpromotores.promotor'

    pao_include_in_budget = fields.Boolean(string='Include in Budget',default=False)