from odoo import fields, models, api, _
from logging import getLogger
from odoo.exceptions import ValidationError

_logger = getLogger(__name__)

class SaleOrder(models.Model):
    _name='pao.audit.blockout.dates'
    _description = 'PAO Audit Blockout Dates'
    _order = 'start_date'

    reason = fields.Char(string="Reason")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_('The start date must be before the end date.'))
