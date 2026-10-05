# -*- coding: utf-8 -*-
from odoo import fields, models


class PaoQuoteScheme(models.Model):
    _name = 'pao.quote.scheme'
    _description = 'Audit Scheme'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company')
    use_long_intro = fields.Boolean(
        string='Use Long Introduction',
        help="Quotations including this scheme print the long introduction (Azzule platform paragraph).",
    )
    block_ids = fields.Many2many(
        comodel_name='pao.quote.block',
        relation='pao_quote_block_scheme_rel',
        column1='scheme_id',
        column2='block_id',
        string='Information Blocks',
        help="Blocks printed when a quotation includes a product of this scheme.",
    )
    product_tmpl_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='pao_quote_scheme_id',
        string='Products',
    )
