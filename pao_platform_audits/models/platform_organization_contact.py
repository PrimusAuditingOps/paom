from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoPlatformOrganizationContact(models.Model):
    _name = "pao.platform.organization.contact"
    _description = "PAO Platform Organization Contact"

    name = fields.Char(
        required=True,
        string= "name",
    )
    email = fields.Char(
        string= "email",
        required=True,
    )
    organization_id = fields.Many2one(
        comodel_name='pao.platform.organization',
        string='Organization',
        ondelete='restrict',
    )    
    