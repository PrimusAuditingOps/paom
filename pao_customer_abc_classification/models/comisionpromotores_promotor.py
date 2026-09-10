# -*- coding: utf-8 -*-
from odoo import models


class ComisionpromotoresPromotor(models.Model):
    _name = 'comisionpromotores.promotor'
    _inherit = ['comisionpromotores.promotor', 'pao.abc.classification.mixin']
