from asyncore import read
from itertools import product
from odoo import tools
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoDegree(models.Model):
    _name = 'pao.degree'
    _description = 'Degree'

    name = fields.Char(
        string="Name",
        translate=True,

    )