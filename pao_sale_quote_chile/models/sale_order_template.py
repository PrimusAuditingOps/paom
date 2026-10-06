# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    pao_quote_format_template = fields.Html(
        string='Chile Quotation Format',
        help="Design of the Chile quotation format for quotations using this template. "
             "Placeholders: [[NUMERO]], [[CLIENTE]], [[CONTACTO]], [[EMAIL]], [[TELEFONO]], [[FECHA]], "
             "[[SALUDO]], [[TABLAS]], [[FIRMA]]. Uses the default format of the company when empty.",
    )
