from odoo import fields, models

class ResPartner(models.Model):
    _inherit='res.partner'

    ctm_cfdi_use = fields.Char(
        string='CFDI use',
    )