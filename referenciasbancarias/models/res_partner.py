from odoo import fields, models, api

class Partner(models.Model):
    
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Modelo para agregar referencias bancarias al modelo res.partner'

    ctm_ref_bank_pesos = fields.Text(
        string = 'Pesos Reference MXN',
    )
    ctm_ref_bank_dolares = fields.Text(
        string = 'Dollar Reference USD',
    )