from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class SaleOrder(models.Model):
    _name='pao.audit.blockout.dates'
    _description = 'PAO Audit Blockout Dates'

    reason = fields.Char(string="Reason")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
