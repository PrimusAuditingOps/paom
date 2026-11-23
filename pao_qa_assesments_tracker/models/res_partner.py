from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ado_is_auditor must be provided by an existing installed module.
    qa_assessment_ids = fields.One2many('pao.qa.assessments', 'partner_id', string='QA Assessments')
    qa_assessment_count = fields.Integer(compute='_compute_qa_assessment_count')
    qa_auditor_type = fields.Selection([
        ('first_time', 'First Time'), ('continuing', 'Continuing')],
        string='QA Auditor Type', default='first_time')
    qa_interval_years_override = fields.Integer(string='Custom Interval (Years)',
                                                  help='Zero uses 2 or 5 years based on auditor type.')
    qa_interval_years = fields.Integer(compute='_compute_qa_interval_years', string='Interval (Years)')
    qa_last_assessment_date = fields.Date(compute='_compute_qa_last_date', store=True,
                                          string='Last Completed QA Assessment')
    qa_next_assessment_calculated_date = fields.Date(compute='_compute_qa_calculated_date',
                                                       string='Calculated Next QA Assessment')
    qa_next_assessment_manual_date = fields.Date(string='Manual Next QA Assessment Date')
    qa_next_assessment_date = fields.Date(compute='_compute_qa_next_date', store=True,
                                           string='Effective Next QA Assessment Date')
    qa_responsible_id = fields.Many2one('res.users', string='QA Responsible',
                                        domain=[('share', '=', False)])
    qa_follower_user_ids = fields.Many2many('res.users', 'pao_qa_partner_follower_rel',
                                            'partner_id', 'user_id', string='QA Notification Users',
                                            domain=[('share', '=', False)])

    @api.depends('qa_assessment_ids')
    def _compute_qa_assessment_count(self):
        for partner in self:
            partner.qa_assessment_count = len(partner.qa_assessment_ids)

    @api.depends('qa_auditor_type', 'qa_interval_years_override')
    def _compute_qa_interval_years(self):
        for partner in self:
            partner.qa_interval_years = partner.qa_interval_years_override or (2 if partner.qa_auditor_type == 'first_time' else 5)

    @api.depends('qa_assessment_ids.state', 'qa_assessment_ids.assessment_date')
    def _compute_qa_last_date(self):
        for partner in self:
            dates = partner.qa_assessment_ids.filtered(
                lambda a: a.state == 'completed' and a.assessment_date).mapped('assessment_date')
            partner.qa_last_assessment_date = max(dates) if dates else False

    @api.depends('qa_last_assessment_date', 'qa_interval_years')
    def _compute_qa_calculated_date(self):
        for partner in self:
            partner.qa_next_assessment_calculated_date = (partner.qa_last_assessment_date + relativedelta(years=partner.qa_interval_years)) if partner.qa_last_assessment_date else False

    @api.depends('qa_next_assessment_manual_date', 'qa_next_assessment_calculated_date')
    def _compute_qa_next_date(self):
        for partner in self:
            partner.qa_next_assessment_date = partner.qa_next_assessment_manual_date or partner.qa_next_assessment_calculated_date

    @api.constrains('qa_interval_years_override')
    def _check_interval(self):
        from odoo.exceptions import ValidationError
        from odoo import _
        for partner in self:
            if partner.qa_interval_years_override < 0:
                raise ValidationError(_('The custom QA interval cannot be negative.'))

    def _qa_recompute_next_date(self):
        # Stored computed fields are updated automatically by Odoo dependencies.
        return True

    def action_view_qa_assessments(self):
        self.ensure_one()
        action = self.env.ref('pao_qa_assesments_tracker.action_qa_assessments').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action
