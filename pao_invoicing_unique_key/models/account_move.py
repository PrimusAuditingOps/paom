from odoo import fields, models

class AccountMove(models.Model):
    _inherit='account.move'

    def _get_sage_key(self):
        for rec in self:
            rec.piuk_sage_key = ""
            if rec.name and rec.name != "/" and rec.move_type == "out_invoice":
                name = rec.name
                year = name[6:-8]
                month = name[9:-5]
                consecutive = name[12:]
                number = 0
                if consecutive.isdigit():
                    number = int(consecutive)
                
                rec.piuk_sage_key = year+month+str(number)

    piuk_sage_key = fields.Char(
        compute = _get_sage_key,
        string = 'Sage key',
        readonly = True,
    )