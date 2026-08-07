from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class SurveyUserInputExtended(models.Model):
    _inherit = 'survey.user_input'

    registration_number = fields.Char(
        string='Registration Number',
        help='Registration number of the audited organization (PGFSNumber)',
    )
    organization_name = fields.Char(
        string='Organization Name',
        help='Name of the organization that received the audit service.',
    )
    app_id = fields.Char(
        string='Application ID',
        help='Identifier of the application in Azzule PrimusGFS.',
    )
    audit_id = fields.Char(
        string='Audit ID',
        help='Identifier of the audit service in Azzule PrimusGFS.',
    )
    certified_date = fields.Date(
        string='Certified Date',
        help='Date when the audit service was certified.',
    )
    coordinator_name = fields.Char(
        string='Coordinator Name',
        help='Name of the operations specialist who coordinated the service.',
    )
    auditor_name = fields.Char(
        string='Auditor Name',
        help='Name of the auditor who performed the service in the field.',
    )
    audit_state = fields.Char(
        string='State',
        help='State where the audit was conducted.',
    )
    audit_country = fields.Char(
        string='Country',
        help='Country where the audit was conducted.',
    )
    contact_name = fields.Char(
        string='Contact Name(s)'
    )
    contact_email = fields.Char(
        string='Contact Email(s)'
    )

    compliment_theme_ids = fields.Many2many(
        comodel_name='survey.compliment.tag',
        relation='survey_input_compliment_tag_rel',
        column1='input_id',
        column2='tag_id',
        string='Compliment Tags',
    )
    complaint_theme_ids = fields.Many2many(
        comodel_name='survey.complaint.tag',
        relation='survey_input_complaint_tag_rel',
        column1='input_id',
        column2='tag_id',
        string='Complaint Tags',
    )

    imported_from_file = fields.Boolean(
        string='Imported from File',
        default=False,
        copy=False,
    )
    
    has_compliment_answer = fields.Boolean(
        string='Has Compliment Answer',
        compute='_compute_dashboard_feedback_flags',
        store=True,
    )

    has_complaint_answer = fields.Boolean(
        string='Has Complaint Answer',
        compute='_compute_dashboard_feedback_flags',
        store=True,
    )
    
    def get_start_url(self, idx=None):
        self.ensure_one()
        url = '%s?answer_token=%s' % (self.survey_id.get_start_url(), self.access_token)
        if idx is not None:
            url += '&idx=%s' % idx
        _logger.warning('get_start_url: idx=%s, url=%s', idx, url)
        return url

    @api.depends('user_input_line_ids.dashboard_feedback_type')
    def _compute_dashboard_feedback_flags(self):

        for user_input in self:

            feedbacks = user_input.user_input_line_ids.mapped(
                'dashboard_feedback_type'
            )

            user_input.has_compliment_answer = (
                'compliment' in feedbacks
            )

            user_input.has_complaint_answer = (
                'complaint' in feedbacks
            )

    def get_compliment_tags_display(self):
        self.ensure_one()
        return ', '.join(self.compliment_theme_ids.mapped('name'))

    def get_complaint_tags_display(self):
        self.ensure_one()
        return ', '.join(self.complaint_theme_ids.mapped('name'))
    
class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    dashboard_feedback_type = fields.Selection(
        [
            ('compliment', 'Compliment'),
            ('complaint', 'Complaint'),
        ],
        string='Feedback Type',
        compute='_compute_dashboard_feedback_type',
        store=True,
    )

    @api.depends(
        'suggested_answer_id',
        'value_char_box',
        'value_numerical_box',
        'question_id.dashboard_feedback_type',
        'question_id.dashboard_trigger_value',
    )
    def _compute_dashboard_feedback_type(self):

        for line in self:
            line.dashboard_feedback_type = False

            question = line.question_id

            if (not question.dashboard_feedback_type or not question.dashboard_trigger_value):
                continue

            value = None

            # Multiple choice
            if line.suggested_answer_id:
                value = (
                    line.suggested_answer_id.value or ''
                ).strip().lower()

            # Text
            elif line.value_char_box:
                value = (
                    line.value_char_box or ''
                ).strip().lower()

            # Numerical
            elif line.value_numerical_box is not None:
                value = str(
                    line.value_numerical_box
                ).strip().lower()

            trigger = (
                question.dashboard_trigger_value
                .strip()
                .lower()
            )

            if value == trigger:
                line.dashboard_feedback_type = (
                    question.dashboard_feedback_type
                )
