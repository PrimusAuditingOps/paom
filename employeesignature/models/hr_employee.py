from odoo import fields, models



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    es_sign_signature = fields.Binary(string="Digital Signature")