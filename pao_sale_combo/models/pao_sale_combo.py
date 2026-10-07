# -*- coding: utf-8 -*-
from odoo import api, fields, models

# The combos are only used by the Chilean company.
COMBO_COUNTRY_CODE = 'CL'


def is_combo_company(company):
    return company.country_id.code == COMBO_COUNTRY_CODE


class PaoSaleCombo(models.Model):
    _name = 'pao.sale.combo'
    _description = 'Sale Combo'
    _order = 'sequence, name'
    _check_company_auto = True

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
    )
    line_ids = fields.One2many(
        comodel_name='pao.sale.combo.line',
        inverse_name='combo_id',
        string='Products',
        copy=True,
    )
    product_count = fields.Integer(string='# Products', compute='_compute_product_count')

    @api.depends('line_ids')
    def _compute_product_count(self):
        for combo in self:
            combo.product_count = len(combo.line_ids)


class PaoSaleComboLine(models.Model):
    _name = 'pao.sale.combo.line'
    _description = 'Sale Combo Product'
    _order = 'sequence, id'
    _check_company_auto = True

    combo_id = fields.Many2one(
        comodel_name='pao.sale.combo',
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(related='combo_id.company_id', store=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        check_company=True,
        domain="[('sale_ok', '=', True)]",
    )

    _sql_constraints = [
        ('combo_product_uniq', 'unique(combo_id, product_id)', 'A product can only be once in the same combo.'),
    ]
