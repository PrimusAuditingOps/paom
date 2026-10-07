# -*- coding: utf-8 -*-
from odoo import fields, models


class PaoQuoteRate(models.Model):
    _name = 'pao.quote.rate'
    _description = 'Quotation Rate Sheet'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.company)
    content = fields.Html(
        string='Format',
        help="Rate sheet sent to the customer. Placeholders: [[NUMERO]], [[CLIENTE]], [[CONTACTO]], [[EMAIL]], "
             "[[TELEFONO]], [[PAIS]], [[FECHA]], [[SALUDO]] and [[FIRMA]] (signature image).",
    )
    template_ids = fields.One2many(
        comodel_name='sale.order.template',
        inverse_name='pao_quote_rate_id',
        string='Quotation Templates',
    )
