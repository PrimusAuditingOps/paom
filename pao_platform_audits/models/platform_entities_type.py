from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoPlatformEntitiesType(models.Model):
    _name = "pao.platform.entities.type"
    _description = "PAO Platform Entities Type"

    name = fields.Char(
        required=True,
        string= "name",
    )
    entity_ids = fields.One2many(
        comodel_name='pao.platform.entities',
        inverse_name='entity_type_id',
        string='Entities',
    )