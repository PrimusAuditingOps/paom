from odoo import fields, models, api

class PaoAuditSchemeAddon(models.Model):
    _name = "pao.audit.scheme.addon"
    _description = "PAO Audit Scheme Addon"
    _rec_name = 'name'

    name = fields.Char("Name")