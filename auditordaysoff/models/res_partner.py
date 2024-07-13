from odoo import fields, models, api



class ResPartner(models.Model):
    _inherit = 'res.partner'

    ado_is_auditor = fields.Boolean(string = "Is an auditor", default = False)