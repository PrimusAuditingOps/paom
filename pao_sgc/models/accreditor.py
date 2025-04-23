from odoo import models, fields


class Accreditor(models.Model):
    _name = 'pao.sgc.accreditor'
    _description = "PAO Accreditor/ Approver of the scheme"
    
    name = fields.Char(
        string='Accreditor/ Approver', 
        required=True,
    )
                    
