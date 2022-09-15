from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class PaoWorkZone(models.Model):
    _name = 'pao.work.zone'
    _description = 'Work Zone'

    _sql_constraints = [
        ('name_unique', 'unique(name)', _('Work Zone already exists!'))
    ]
    name = fields.Char(
        string="Work Zone",
        required=True,
    )
    