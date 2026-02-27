from odoo import models, fields, api
from logging import getLogger

_logger = getLogger(__name__)

class SATCFDIPackages(models.Model):
    _name = "pao.sat.cfdi.packages"
    _description = "PAO SAT CFDI packages"
    
    name = fields.Char(
        string="name",
        required=True,
    )
    sat_cfdi_request_id = fields.Many2one(
        'pao.sat.cfdi.request',
        string='SAT CDFI request',
        ondelete='cascade'
    )