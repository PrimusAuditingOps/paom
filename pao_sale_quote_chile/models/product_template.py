# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pao_quote_scheme_id = fields.Many2one(
        comodel_name='pao.quote.scheme',
        string='Audit Scheme',
        help="Scheme of the service or add-on. Defines which information blocks the Chile quotation prints.",
    )
    pao_quote_table_id = fields.Many2one(
        comodel_name='pao.quote.table',
        string='Quotation Table Format',
        help="Format used by the table where this product is the first row.",
    )
    pao_quote_name = fields.Char(
        string='Quotation Name',
        help="Name printed in the Chile quotation. Uses the product name when empty. "
             "Footnote marks can be typed directly, e.g. 'GLOBALG.A.P. (v.6 GFS)¹'.",
    )
    pao_quote_combine = fields.Boolean(
        string='Combine With Previous Line',
        help="In the Chile quotation, print this product in the same row as the previous line, "
             "e.g. 'GLOBALG.A.P. + Nurture Add-On' with the summed price.",
    )
    pao_quote_note = fields.Html(
        string='Quotation Note',
        help="Footnote printed below the table that contains this product.",
    )
