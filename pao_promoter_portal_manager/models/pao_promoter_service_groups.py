from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class PaoPromoterServiceGroups(models.Model):
    _name = 'pao.promoter.service.groups'
    _description = 'Promoter Service Groups'

    name = fields.Char(
        string="Name",
        required=True,
    )
    image = fields.Image(
        string="Group image", 
        max_width=1024, 
        max_height=1024,
        required=True,
    )