from odoo import models, fields

class SurveyComplimentTag(models.Model):
    _name = 'survey.compliment.tag'
    _description = 'Compliment Theme Tag'
    _order = 'name asc'

    name = fields.Char(string='Tag', required=True, translate=True)
    color = fields.Integer(string='Color Index', default=0)
    active = fields.Boolean(default=True)

    user_input_ids = fields.Many2many(
        'survey.user_input',
        'survey_input_compliment_tag_rel',
        'tag_id',
        'input_id',
        string='Survey Inputs',
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The compliment tag name must be unique.'),
    ]
