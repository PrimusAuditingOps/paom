# -*- coding: utf-8 -*-
from odoo import fields, models


class PaoQuoteCategory(models.Model):
    _name = 'pao.quote.category'
    _description = 'Quotation Category'
    _order = 'sequence, id'

    name = fields.Char(required=True, help="Numbered heading of the quotation, e.g. 'Auditorías de Campo'.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company')
