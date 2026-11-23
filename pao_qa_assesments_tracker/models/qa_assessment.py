from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PaoQaAssessment(models.Model):
    _name = 'pao.qa.assessments'
    _description = 'QA Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'target_date desc, id desc'

    name = fields.Char(compute='_compute_name', store=True)
    partner_id = fields.Many2one('res.partner', string='Auditor', required=True,
                                 ondelete='restrict', index=True, tracking=True,
                                 domain=[('ado_is_auditor', '=', True)])
    qa_history_ids = fields.One2many(related='partner_id.qa_assessment_ids', string='Assessment History', readonly=True)
    first_name = fields.Char(string='First Name', compute='_compute_contact', store=True)
    last_name = fields.Char(string='Last Name', compute='_compute_contact', store=True)
    email = fields.Char(compute='_compute_contact', store=True)
    country_id = fields.Many2one('res.country', compute='_compute_contact', store=True)
    assessment_type = fields.Selection([
        ('initial', 'Initial'), ('witness', 'Witness'),
        ('other', 'Other')], string='Assessment Type', tracking=True)
    assessment_scope = fields.Char(string='Assessment Scope', tracking=True)
    priority = fields.Selection([
        ('0', 'Low'), ('1', 'Medium'), ('2', 'High'), ('3', 'Critical')],
        default='1', tracking=True)
    state = fields.Selection([
        ('not_scheduled', 'Not Scheduled'), ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'), ('completed', 'Completed'),
        ('cancelled', 'Cancelled')], default='not_scheduled', required=True,
        tracking=True, index=True)
    assessment_date = fields.Date(string='Date', tracking=True,
                                  help='Actual completion date; required to mark completed.')
    target_date = fields.Date(string='Target Date', index=True, tracking=True,
                              help='Planned due date; distinct from actual completion date.')
    assessor_id = fields.Many2one('res.users', string='Assessor', domain=[('share', '=', False)])
    notes = fields.Text(string='Notes')
    ops_notes = fields.Text(string='Ops Notes')
    responsible_id = fields.Many2one('res.users', string='Responsible',
                                     domain=[('share', '=', False)], tracking=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    result = fields.Selection([('passed', 'Passed'), ('failed', 'Failed'),
                               ('other', 'Other')], tracking=True)
    source = fields.Selection([('manual', 'Manual'), ('cron', 'Automatic'),
                               ('import', 'Imported')], default='manual', readonly=True)
    tracker_year = fields.Integer(string='Source Sheet Year', readonly=True)
    cycle_date = fields.Date(string='Cycle Date', index=True, readonly=True,
                             help='Cycle identifier for automatic records.')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
                                 required=True)

    @api.depends('partner_id', 'target_date')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s - %s' % (rec.partner_id.display_name or _('QA Assessment'),
                                    rec.target_date or _('Unscheduled'))

    @api.depends('partner_id', 'partner_id.name', 'partner_id.email', 'partner_id.country_id')
    def _compute_contact(self):
        for rec in self:
            partner = rec.partner_id
            rec.first_name = partner._fields.get('first_name') and partner.first_name or (partner.name or '').split(' ')[0]
            rec.last_name = partner._fields.get('last_name') and partner.last_name or ' '.join((partner.name or '').split(' ')[1:])
            rec.email = partner.email
            rec.country_id = partner.country_id

    @api.constrains('partner_id')
    def _check_auditor(self):
        for rec in self:
            if not rec.partner_id.ado_is_auditor:
                raise ValidationError(_('Only contacts marked as auditors can have QA assessments.'))

    @api.constrains('state', 'assessment_date')
    def _check_completion_date(self):
        for rec in self:
            if rec.state == 'completed' and not rec.assessment_date:
                raise ValidationError(_('A completed assessment requires an actual assessment date.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._subscribe_relevant_users()
        records.mapped('partner_id')._qa_recompute_next_date()
        return records

    def write(self, vals):
        old_partners = self.mapped('partner_id')
        result = super().write(vals)
        if {'partner_id', 'responsible_id'} & set(vals):
            self._subscribe_relevant_users()
        if vals.get('state') == 'completed':
            # A manual date applies to the cycle being completed, not indefinitely.
            for partner in self.mapped('partner_id'):
                if partner.qa_next_assessment_manual_date:
                    partner.qa_next_assessment_manual_date = False
        if {'partner_id', 'state', 'assessment_date'} & set(vals):
            (old_partners | self.mapped('partner_id'))._qa_recompute_next_date()
        return result

    def unlink(self):
        partners = self.mapped('partner_id')
        result = super().unlink()
        partners._qa_recompute_next_date()
        return result

    def _subscribe_relevant_users(self):
        for rec in self:
            users = rec.responsible_id | rec.partner_id.qa_follower_user_ids
            partner_ids = users.mapped('partner_id').ids
            if partner_ids:
                rec.message_subscribe(partner_ids=partner_ids)

    @api.model
    def _cron_generate_due_assessments(self):
        today = fields.Date.context_today(self)
        horizon = today + relativedelta(months=3)
        partners = self.env['res.partner'].search([
            ('ado_is_auditor', '=', True),
            ('qa_next_assessment_date', '!=', False),
            ('qa_next_assessment_date', '<=', horizon),
        ])
        for partner in partners:
            cycle = partner.qa_next_assessment_date
            # One outstanding record per auditor, even if the due date is edited.
            outstanding = self.search_count([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['not_scheduled', 'scheduled', 'in_progress']),
            ])
            if outstanding:
                continue
            rec = self.create({
                'partner_id': partner.id,
                'target_date': cycle,
                'cycle_date': cycle,
                'responsible_id': partner.qa_responsible_id.id or False,
                'source': 'cron',
            })
            users = partner.qa_responsible_id | partner.qa_follower_user_ids
            for user in users:
                rec.activity_schedule('mail.mail_activity_data_todo', user_id=user.id,
                                      summary=_('New QA assessment due'),
                                      note=_('QA assessment target date: %s') % cycle)
            rec.message_post(body=_('QA assessment generated automatically for target date %s.') % cycle)
