from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
class PaaAuditorAssignmentAuditsPertMonth(models.Model):
    _name = 'paoassignmentauditor.auditsquantitypermonth'
    _description = 'Auditor assignment Audits quantity per Month'
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
    audit_quantity = fields.Integer(
        string="Number of Audit",
        default=0,
    )
    configuration_id = fields.Many2one(
        comodel_name='paoassignmentauditor.configuration.audit.quantity',
        string='configuration', 
        ondelete='set null',
    )
   