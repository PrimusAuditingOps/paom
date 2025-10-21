from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoPlatformCoordinator(models.Model):
    _name = "pao.platform.coordinator"
    _description = "PAO Platform Coordinator"

    name = fields.Char(
        required=True,
        string= "name",
    )
    user_id = fields.Many2one(
        'res.users', 
        string="Operations Specialist",
        ondelete='set null', 
        index=True,
        domain = [('share','=',False)]
    )
    