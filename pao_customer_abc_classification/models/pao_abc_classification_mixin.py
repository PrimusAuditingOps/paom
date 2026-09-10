# -*- coding: utf-8 -*-
from odoo import fields, models


class PaoAbcClassificationMixin(models.AbstractModel):
    _name = 'pao.abc.classification.mixin'
    _description = 'Campos de Categoría ABC compartidos por Contactos, Grupos y Promotores'

    categoria_abc_id = fields.Many2one(
        comodel_name='pao.abc.category', string='Categoría ABC',
    )
    abc_sales_amount = fields.Float(
        string='Ventas USD (temporada ABC)', digits=(16, 2), readonly=True,
        help='Total facturado en USD (sin impuestos, solo productos '
             'comisionables) usado para calcular la Categoría ABC.',
    )
    abc_season = fields.Char(
        string='Temporada ABC', readonly=True,
        help='Temporada (septiembre-agosto) sobre la que se calculó '
             'la Categoría ABC vigente.',
    )
