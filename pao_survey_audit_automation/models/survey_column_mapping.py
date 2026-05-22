from odoo import models, fields, api
from odoo.exceptions import ValidationError

AUDIT_FIELDS = [
    ('contact_email',       'Contact Email(s) *'),
    ('contact_name',        'Contact Name(s)'),
    ('organization_name',   'Organization Name'),
    ('registration_number', 'Registration Number'),
    ('app_id',              'Application ID'),
    ('audit_id',            'Audit ID'),
    ('certified_date',      'Certified Date'),
    ('coordinator_name',    'Coordinator Name'),
    ('auditor_name',        'Auditor Name'),
    ('audit_state',         'State'),
    ('audit_country',       'Country'),
]

class SurveyColumnMapping(models.Model):
    _name = 'survey.column.mapping'
    _description = 'Survey file column mapping'
    _order = 'sequence asc'

    survey_id = fields.Many2one(
        'survey.survey',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    field_name = fields.Selection(
        selection=AUDIT_FIELDS,
        string='Field Name',
        required=True,
    )
    column_name = fields.Char(
        string='Column name in file',
        required=True,
        help='Exact column header name as it appears in the file.',
    )

    @api.constrains('survey_id', 'field_name')
    def _check_unique_field(self):
        for rec in self:
            duplicate = self.search([
                ('survey_id', '=', rec.survey_id.id),
                ('field_name', '=', rec.field_name),
                ('id', '!=', rec.id),
            ])
            if duplicate:
                raise ValidationError(
                    'Each field can only be mapped once per survey.'
                )