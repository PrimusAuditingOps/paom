from odoo import models, api
from num2words import num2words

class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.model
    def pao_amount_to_text_check(self, amount):
        amount_int = int(amount)
        amount_dec = int(round((amount - amount_int) * 100))
        words = num2words(amount_int, lang='en').upper()
        return f"{words} AND {amount_dec:02d}/100"