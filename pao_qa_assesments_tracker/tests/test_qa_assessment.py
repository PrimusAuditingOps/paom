from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tests.common import TransactionCase
from odoo import fields


class TestQaAssessment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.auditor = self.env['res.partner'].create({'name': 'Test Auditor', 'ado_is_auditor': True})

    def test_five_year_cycle(self):
        self.auditor.qa_auditor_type = 'continuing'
        self.env['pao.qa.assessments'].create({
            'partner_id': self.auditor.id, 'state': 'completed',
            'assessment_date': date(2022, 6, 15),
        })
        self.assertEqual(self.auditor.qa_next_assessment_date, date(2027, 6, 15))

    def test_manual_override(self):
        self.auditor.qa_next_assessment_manual_date = date(2028, 9, 1)
        self.assertEqual(self.auditor.qa_next_assessment_date, date(2028, 9, 1))

    def test_cron_idempotent(self):
        self.auditor.qa_next_assessment_manual_date = fields.Date.today()
        Model = self.env['pao.qa.assessments']
        Model._cron_generate_due_assessments()
        Model._cron_generate_due_assessments()
        self.assertEqual(Model.search_count([('partner_id', '=', self.auditor.id)]), 1)
