# -*- coding: utf-8 -*-
from odoo import fields, models


class PaoQuoteBlock(models.Model):
    _name = 'pao.quote.block'
    _description = 'Quotation Information Block'
    _order = 'position, sequence, id'

    name = fields.Char(string='Title', required=True)
    show_title = fields.Boolean(string='Print Title', default=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company')
    position = fields.Selection(
        selection=[
            ('billing', 'Billing Considerations'),
            ('additional', 'Additional Information'),
            ('annex', 'Annex (new page)'),
        ],
        default='additional',
        required=True,
    )
    content = fields.Html()
    apply_always = fields.Boolean(
        string='Always Print',
        help="Print in every quotation. Otherwise it is printed only when the quotation includes one of its schemes.",
    )
    scheme_ids = fields.Many2many(
        comodel_name='pao.quote.scheme',
        relation='pao_quote_block_scheme_rel',
        column1='block_id',
        column2='scheme_id',
        string='Schemes',
    )
    audience = fields.Selection(
        selection=[
            ('all', 'All Customers'),
            ('national', 'Customers in the Company Country'),
            ('foreign', 'Foreign Customers'),
        ],
        default='all',
        required=True,
    )
