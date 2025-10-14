from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoPlatformEntities(models.Model):
    _name = "pao.platform.entities"
    _description = "PAO Platform Entities"

    name = fields.Char(
        required=True,
        string= "name",
    )  
    entity_type_id = fields.Many2one(
        comodel_name='pao.platform.entities.type',
        string='Entity Type',
        ondelete='restrict',
    )    
    