from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoOffices(models.Model):
    _name = "pao.offices"
    _description = "PAO Offices"
   
    name = fields.Char(
        required=True,
        string= "Name",
    )
    customer_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='pao_office_id',
        string='Customers',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company) 