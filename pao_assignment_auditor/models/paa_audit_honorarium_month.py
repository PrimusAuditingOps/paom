from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
class PaaAuditorAssignmentAuditsHonorariumPertMonth(models.Model):
    _name = 'paoassignmentauditor.auditshonorariumpermonth'
    _description = 'Auditor assignment Audits honorarium per Month'
    _rec_name = 'month'
    _order = 'month asc'


    month = fields.Selection(
        selection=[
            ("01", "January"),
            ("02", "Febrary"),
            ("03", "March"),
            ("04", "April"),
            ("05", "May"),
            ("06", "June"),
            ("07", "July"),
            ("08", "August"),
            ("09", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Month", 
        copy=False,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
    )
    audit_honorarium_total = fields.Monetary(
        string="Total honorarium of audits",
        currency_field='currency_id',
        default=0,
    )
    configuration_id = fields.Many2one(
        comodel_name='paoassignmentauditor.configuration.audit.honorarium',
        string='configuration', 
        ondelete='set null',
    )
   