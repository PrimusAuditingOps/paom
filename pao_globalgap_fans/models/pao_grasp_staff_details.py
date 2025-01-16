from odoo import fields, models, api, _
from logging import getLogger

class PaoGraspStaffDetails(models.Model):
    _name = "pao.grasp.staff.details"
    _description = "GRASP Staff Details"
    
    employees_type = fields.Selection(
        selection=[
            ('permanent', "Permanentes"),
            ('temp', "Temporales"),
            ('subcontracted', "Subcontratados"),
        ],
        string="Employees Type",
        readonly=True
    )
    
    locals_male_quantity = fields.Char(string="National (Men)", default=0, readonly=True)
    locals_female_quantity = fields.Char(string="National (Women)", default=0, readonly=True)
    foreigners_male_quantity = fields.Char(string="Foregin (Men)", default=0, readonly=True)
    foreigners_female_quantity = fields.Char(string="Foregin (Women)", default=0, readonly=True)
    
    production_site_id = fields.Many2one(
        comodel_name='pao.globalgap.production.site',
        string='Production Site',
        ondelete='cascade',
        readonly=True
    )
    