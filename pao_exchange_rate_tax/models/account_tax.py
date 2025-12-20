""" Import Library """
from odoo import models, fields, _



class AccountTax(models.Model):
    """ Inherit account.tax """
    _inherit = 'account.tax'

    use_cash_basis_trans_account = fields.Boolean(
        string="Use cash basis transaction account in exchange rate",)
