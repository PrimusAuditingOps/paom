# -*- coding: utf-8 -*-
from odoo import models


class CustomerGroupsGroup(models.Model):
    _name = 'customergroups.group'
    _inherit = ['customergroups.group', 'pao.abc.classification.mixin']
