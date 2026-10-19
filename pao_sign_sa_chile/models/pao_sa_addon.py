# -*- coding: utf-8 -*-
from odoo import fields, models


class PaoSaAddon(models.Model):
    _name = 'pao.sa.addon'
    _description = 'SA Add-On'
    _order = 'sequence, name'

    name = fields.Char(required=True, help="Name printed next to the checkbox of point 7, e.g. 'NURTURE'.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
    )
    product_tmpl_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='pao_sa_addon_id',
        string='Products',
    )
