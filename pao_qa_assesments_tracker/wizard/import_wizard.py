import base64
import csv
import io
from datetime import datetime, date

from odoo import fields, models, _
from odoo.exceptions import UserError


class PaoQaImportWizard(models.TransientModel):
    _name = 'pao.qa.import.wizard'
    _description = 'Import historical QA assessments from CSV'

    file = fields.Binary(string='CSV File', required=True)
    filename = fields.Char()
    dry_run = fields.Boolean(string='Validate Only', default=True)
    report = fields.Text(readonly=True)

    def action_import(self):
        self.ensure_one()
        try:
            payload = base64.b64decode(self.file).decode('utf-8-sig')
            rows = list(csv.DictReader(io.StringIO(payload)))
        except (UnicodeError, csv.Error, ValueError) as exc:
            raise UserError(_('Invalid UTF-8 CSV file: %s') % exc)
        required = {'First Name', 'Last Name', 'Email', 'Country', 'Assessment Type',
                    'Assessment Scope', 'Priority', 'Status', 'Date', 'Assessor', 'Notes'}
        if not rows:
            raise UserError(_('No data rows found.'))
        if not required.issubset(rows[0]):
            raise UserError(_('Missing CSV columns: %s') % ', '.join(sorted(required - set(rows[0]))))
        problems, ready = [], []
        Partner = self.env['res.partner']
        Assessment = self.env['pao.qa.assessments']
        state_map = {'completed': 'completed', 'done': 'completed', 'scheduled': 'scheduled',
                     'not scheduled': 'not_scheduled', 'in progress': 'in_progress',
                     'cancelled': 'cancelled', 'canceled': 'cancelled'}
        priority_map = {'low': '0', 'medium': '1', 'high': '2', 'critical': '3'}
        type_map = {'initial': 'initial', 'witness': 'witness', 'other': 'other'}
        for idx, row in enumerate(rows, start=2):
            try:
                email = (row.get('Email') or '').strip()
                first = (row.get('First Name') or '').strip()
                last = (row.get('Last Name') or '').strip()
                if not email:
                    raise ValueError('Email is required to match an auditor')
                matches = Partner.search([('ado_is_auditor', '=', True), ('email', '=ilike', email)])
                if len(matches) != 1:
                    raise ValueError('Expected one auditor matching email %s, found %s' % (email, len(matches)))
                partner = matches[0]
                if first and first.casefold() not in (partner.name or '').casefold():
                    raise ValueError('First name does not match contact')
                if last and last.casefold() not in (partner.name or '').casefold():
                    raise ValueError('Last name does not match contact')
                state_text = (row.get('Status') or '').strip().lower()
                if state_text not in state_map:
                    raise ValueError('Unknown status: %s' % state_text)
                state = state_map[state_text]
                raw_date = (row.get('Date') or '').strip()
                actual_date = False
                if raw_date:
                    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'):
                        try:
                            actual_date = datetime.strptime(raw_date, fmt).date()
                            break
                        except ValueError:
                            pass
                    if not actual_date:
                        raise ValueError('Ambiguous or invalid date: %s' % raw_date)
                if state == 'completed' and not actual_date:
                    raise ValueError('Completed assessment without a date')
                typ = (row.get('Assessment Type') or '').strip().lower()
                if typ not in type_map:
                    raise ValueError('Unknown assessment type: %s' % typ)
                prio = (row.get('Priority') or 'Medium').strip().lower()
                if prio not in priority_map:
                    raise ValueError('Unknown priority: %s' % prio)
                vals = {
                    'partner_id': partner.id, 'assessment_type': type_map[typ],
                    'assessment_scope': (row.get('Assessment Scope') or '').strip(),
                    'priority': priority_map[prio], 'state': state,
                    'assessment_date': actual_date if state == 'completed' else False,
                    'target_date': actual_date if state != 'completed' else False,
                    'notes': row.get('Notes') or False,
                    'ops_notes': row.get('Ops Notes') or False,
                    'source': 'import',
                }
                assessor = (row.get('Assessor') or '').strip()
                if assessor:
                    users = self.env['res.users'].search([('name', '=ilike', assessor), ('share', '=', False)])
                    if len(users) != 1:
                        raise ValueError('Assessor is not uniquely identifiable: %s' % assessor)
                    vals['assessor_id'] = users.id
                year = (row.get('Tracker Year') or '').strip()
                if year:
                    vals['tracker_year'] = int(year)
                # Conservative duplicate detection, including imports from previous runs.
                existing = Assessment.search_count([
                    ('partner_id', '=', partner.id), ('assessment_type', '=', vals['assessment_type']),
                    ('assessment_scope', '=', vals['assessment_scope']),
                    ('assessment_date', '=', vals['assessment_date']),
                    ('target_date', '=', vals['target_date']),
                    ('state', '=', state),
                ])
                if existing:
                    raise ValueError('Possible duplicate assessment; review manually')
                ready.append((idx, vals))
            except (ValueError, TypeError) as exc:
                problems.append('Row %s: %s' % (idx, exc))
        if not self.dry_run and problems:
            raise UserError(_('Import blocked. Fix all issues first:\n%s') % '\n'.join(problems[:50]))
        if not self.dry_run:
            for idx, vals in ready:
                Assessment.create(vals)
        self.report = '%s valid rows; %s errors; %s.\n%s' % (
            len(ready), len(problems), 'Validation only' if self.dry_run else 'Imported',
            '\n'.join(problems[:100]))
        return {'type': 'ir.actions.act_window', 'res_model': self._name,
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}
