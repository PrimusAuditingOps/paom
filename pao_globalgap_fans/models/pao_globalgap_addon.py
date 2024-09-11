from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapAddon(models.Model):
    _name = "pao.globalgap.addon"
    _description = "GLOBALG.A.P. addon"


    name = fields.Char(
        string='Name', 
        copy=False,
        required=True,
        translate=True, 
    )
    is_grasp_module = fields.Boolean(
        string= "Is GRASP module",
        default= False,
    )
    is_fsma_module = fields.Boolean(
        string= "Is FSMA module",
        default= False,
    )