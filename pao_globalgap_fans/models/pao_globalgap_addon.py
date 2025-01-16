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
    
    active = fields.Boolean(string="Active", default=True)
    
    is_grasp_module = fields.Boolean(
        string= "Is GRASP module",
        default= False,
    )
    is_fsma_module = fields.Boolean(
        string= "Is FSMA module",
        default= False,
    )
    
    version_id = fields.Many2many(
        comodel_name='pao.globalgap.version',
        string='Version',
    )
    
    version_ids_list = fields.Char(compute="_compute_version_list")
    
    @api.depends('version_id')
    def _compute_version_list(self):
        for record in self:
            # Extract the IDs from the Many2many field
            ids = record.version_id.ids
            # Generate the string with prefix "v" and join with underscores
            record.version_ids_list = ' '.join(f'v{id}' for id in ids)