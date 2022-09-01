from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
class PaaConfigurationAuditQuantity(models.Model):
    _name = 'paoassignmentauditor.configuration.audit.quantity'
    _description = 'Auditor assignment Audits Configuration'
    _rec_name = 'option'

    
    option = fields.Selection(
        selection=[
            ("auditor", "Auditor"),
            ("month", "Month"),
            ("trimester", "Trimester"),
            ("season", "Season"),
        ],
        string="Option", 
        copy=False,
        default="auditor",
    )
    season_start_month = fields.Selection(
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
        string="Season start month", 
        copy=False,
    )
    season_end_month = fields.Selection(
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
        string="Season end month", 
        copy=False,
    )
    audits_quantity_per_month_ids = fields.One2many(
        comodel_name='paoassignmentauditor.auditsquantitypermonth',
        inverse_name='configuration_id',
        string='Audits per month',
    )
    audit_quantity = fields.Integer(
        string="Number of Audit",
        default=0,
    )
    first_month_audit_quantity = fields.Integer(
        string="First Trimester",
        default=0,
    )
    second_month_audit_quantity = fields.Integer(
        string="Second Trimester",
        default=0,
    )
    third_month_audit_quantity = fields.Integer(
        string="Third Trimester",
        default=0,
    )
    fourth_month_audit_quantity = fields.Integer(
        string="Fourth Trimester",
        default=0,
    )
    @api.onchange('season_start_month')
    def _change_season_start_month(self):
        for rec in self:
            if rec.season_start_month:
                
                value = int(rec.season_start_month)
                if value == 1:
                    rec.season_end_month = '12'
                else:
                    rec.season_end_month = str(value-1).rjust(2, '0')
    