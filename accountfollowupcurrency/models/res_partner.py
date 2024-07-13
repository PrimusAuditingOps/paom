from odoo import api, fields, models, _
from odoo.tools.misc import format_date
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT




class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _update_next_followup_action_date(self, followup_line):
        """ Hot Fix: replace base to resolve the empty aml.date_maturity bug
            Change aml.date_maturity to aml.date_maturity or aml.date
        """
        """Updates the followup_next_action_date of the right account move lines
        """
        self.ensure_one()
        if followup_line:
            next_date = followup_line._get_next_date()
            self.followup_next_action_date = datetime.strftime(next_date, DEFAULT_SERVER_DATE_FORMAT)
            msg = _('Next Reminder Date set to %s', format_date(self.env, self.followup_next_action_date))
            self.message_post(body=msg)

        today = fields.Date.context_today(self)
        previous_levels = self.env['account_followup.followup.line'].search([('delay', '<=', followup_line.delay), ('company_id', '=', self.env.company.id)])
        for aml in self._get_included_unreconciled_aml_ids():
            eligible_levels = previous_levels.filtered(lambda level: (today - (aml.date_maturity or aml.date)).days >= level.delay)
            if eligible_levels:
                aml.followup_line_id = max(eligible_levels, key=lambda level: level.delay)
