from odoo import models, fields

class SurveyComplaintTag(models.Model):
    _name = 'survey.complaint.tag'
    _description = 'Complaint Theme Tag'
    _order = 'name asc'

    name = fields.Char(string='Tag', required=True, translate=True)
    color = fields.Integer(string='Color Index', default=0)
    active = fields.Boolean(default=True)

    user_input_ids = fields.Many2many(
        'survey.user_input',
        'survey_input_complaint_tag_rel',
        'tag_id',
        'input_id',
        string='Survey Inputs',
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The complaint tag name must be unique.'),
    ]
