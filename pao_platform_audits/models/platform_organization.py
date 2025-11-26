from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoPlatformOrganization(models.Model):
    _name = "pao.platform.organization"
    _description = "PAO Platform Organization"

    name = fields.Char(
        required=True,
        string= "name",
    )
    contact_ids = fields.One2many(
        comodel_name='pao.platform.organization.contact',
        inverse_name='organization_id',
        string='Contacts',
    )