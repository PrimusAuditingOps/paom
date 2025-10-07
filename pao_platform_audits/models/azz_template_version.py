from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoAzzTemplateVersion(models.Model):
    _name = "pao.azz.template.version"
    _description = "PAO Azz Template Version"

    name = fields.Char(
        required=True,
        string= "Name", 
        translate=True,
    )
    pao_audit_template = fields.Many2one(
        comodel_name='pao.azz.audit.template',
        string='Audit Template',
        ondelete='restrict',
    )    