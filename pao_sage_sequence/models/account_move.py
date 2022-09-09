from odoo import api, exceptions, fields, models, _
from logging import getLogger

_logger = getLogger(__name__)

class AccountMove(models.Model):
    _inherit='account.move'
    
    pao_sage_folio = fields.Char(
        string = 'folio SAGE',
    )

    
    
    def write(self, vals):

        if self.move_type == "out_invoice" and vals.get('state') == 'posted' and not self.pao_sage_folio:
            seq = 0
            seq = self.env['ir.sequence'].next_by_code('pao.sage.invoice')
            vals['pao_sage_folio'] = str(seq)
        
        result = super(AccountMove, self).write(vals)
        return result