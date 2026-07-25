from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    pao_use_custom_rate = fields.Boolean(
        string="Usar tasa personalizada",
        copy=False,
        help="Si se activa, se utilizará la 'Tasa personalizada' indicada "
            "abajo en vez de la tasa nativa de Odoo (res.currency.rate)  "
            "para generar los apuntes contables en moneda de la compañía.",
    )
    pao_custom_rate = fields.Float(
        string="Tasa personalizada",
        copy=False,
        digits=(16, 6),
        help="Equivalencia: 1 unidad de la moneda del documento = X unidades "
            "de la moneda de la compañía. "
            "Ej: si el documento está en USD y la compañía en CLP, y "
            "1 USD = 858.45 CLP, ingresar 858.45.",
    )

    @api.onchange('pao_use_custom_rate')
    def _onchange_pao_use_custom_rate(self):
        # Sugiere como valor inicial la tasa que Odoo habría usado
        # (moneda documento -> moneda compañía), para que el usuario solo
        # deba ajustarla si corresponde.
        for move in self:
            if move.pao_use_custom_rate and not move.pao_custom_rate:
                line = move.line_ids.filtered(lambda l: l.currency_id and l.currency_rate)[:1]
                if line:
                    move.pao_custom_rate = 1 / line.currency_rate if line.currency_rate else 1.0
                else:
                    move.pao_custom_rate = 1.0

    @api.constrains('pao_use_custom_rate', 'pao_custom_rate')
    def _check_pao_custom_rate(self):
        for move in self:
            if move.pao_use_custom_rate and move.pao_custom_rate <= 0:
                raise ValidationError(_(
                    "La tasa personalizada debe ser mayor a 0 en el documento %s."
                ) % move.display_name)
