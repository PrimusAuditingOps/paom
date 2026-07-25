from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends(
        'currency_id', 'company_id', 'move_id.date',
        'move_id.pao_use_custom_rate', 'move_id.pao_custom_rate',
    )
    def _compute_currency_rate(self):
        # 'currency_rate' representa, en la convención nativa de Odoo,
        # cuantas unidades de la moneda del documento equivalen a 1 unidad
        # de la moneda de la compañía (company -> document). Por eso se
        # invierte la 'tasa personalizada' que el usuario ingresa en el
        # sentido document -> company (ej. 1 USD = 858.45 CLP).
        custom_lines = self.filtered(
            lambda l: l.currency_id
            and l.move_id.pao_use_custom_rate
            and l.move_id.pao_custom_rate
        )
        for line in custom_lines:
            line.currency_rate = 1 / line.move_id.pao_custom_rate

        remaining_lines = self - custom_lines
        if remaining_lines:
            super(AccountMoveLine, remaining_lines)._compute_currency_rate()
