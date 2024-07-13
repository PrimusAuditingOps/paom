from odoo import api, fields, models, _



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    currency_name = fields.Char(related='currency_id.name',
                                string='Currency Name', translate=True)
