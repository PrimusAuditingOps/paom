# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class SurveyQuestionExtended(models.Model):
    _inherit = 'survey.question'

# "Tipo de feedback para dashboard
    dashboard_feedback_type = fields.Selection([
        ('compliment', 'Compliment'),
        ('complaint', 'Complaint'),
        ('max_score_indicator', 'Max Score'), 
    ],
        string='Feedback Type', 
        default=None,
        help='Defines whether this question should be considered as a compliment, complaint or max score indicator in dashboard statistics.',
        copy=False,
    )

    dashboard_trigger_value = fields.Char(
        string='Trigger Value',
        help='Answer value that will trigger this question to be counted in dashboard statistics.'
    )

    @api.constrains('survey_id', 'dashboard_feedback_type')
    def _check_unique_max_score(self):
        for rec in self.filtered(lambda r: r.dashboard_feedback_type == 'max_score_indicator'):
            other = self.search([
                ('survey_id', '=', rec.survey_id.id),
                ('dashboard_feedback_type', '=', 'max_score_indicator'),
                ('id', '!=', rec.id),
            ])
            if other:
                raise ValidationError(
                    _("Only one question can be Max Score Indicator per survey.")
                )
    
    @api.constrains('dashboard_feedback_type','dashboard_trigger_value')
    def _check_trigger_value_required(self):
        for rec in self:
            if (rec.dashboard_feedback_type in ('compliment','complaint',) and not rec.dashboard_trigger_value):
                raise ValidationError(
                    _('Trigger Value is required for Compliment or Complaint questions.')
                )