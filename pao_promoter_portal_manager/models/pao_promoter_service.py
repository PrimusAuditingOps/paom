from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class PaoPromoterService(models.Model):
    _name = 'pao.promoter.service'
    _description = 'Promoter Service'

    name = fields.Char(
        string="Name",
        required=True,
        translate=True, 
    )
    service_group_id = fields.Many2one(
        string="Group",
        comodel_name='pao.promoter.service.groups',
        ondelete='cascade',
        required=True,
    )
    