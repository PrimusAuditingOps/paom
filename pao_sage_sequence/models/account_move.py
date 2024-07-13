from odoo import fields, models



class AccountMove(models.Model):
    _inherit = 'account.move'
    
    pao_sage_folio = fields.Char(string='folio SAGE')  
