# -*- coding: utf-8 -*-
from odoo import fields, models


class PaoQuoteTable(models.Model):
    _name = 'pao.quote.table'
    _description = 'Quotation Table Format'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company')
    category_id = fields.Many2one(
        comodel_name='pao.quote.category',
        string='Category',
        help="Numbered heading under which tables with this format are grouped.",
    )
    style = fields.Selection(
        selection=[
            ('main', 'Main (grey header)'),
            ('module', 'Module (green header)'),
        ],
        default='main',
        required=True,
    )
    header_label = fields.Char(string='Description Column', default='ALTERNATIVAS PARA PREDIOS')
    price_label = fields.Char(
        string='Price Column',
        default='Valor Certificación',
        help="The currency (e.g. 'USD $') is added below this label automatically.",
    )
    band_label = fields.Char(string='Band Label', help="Optional green band printed below the header, e.g. 'Auditorías'.")
    footer_label = fields.Char(
        string='Table Footer',
        default='Valores en USD + Fee GLOBALG.A.P.¹ + Gastos Viaje³ + IVA',
    )
    notes = fields.Html(
        string='Notes (before product notes)',
        help="Printed below the table, before the quotation notes of its products.",
    )
    notes_after = fields.Html(
        string='Notes (after product notes)',
        help="Printed below the table, after the quotation notes of its products.",
    )
    show_total = fields.Boolean(
        string='Show Total',
        help="Print a total row (e.g. organic certification stages). Only when all rows share the same currency.",
    )
    total_label = fields.Char(string='Total Label', default='Total por Servicio de Auditoría:')
