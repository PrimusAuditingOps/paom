from odoo import api, exceptions, fields, models, _
from logging import getLogger
from odoo.tools.misc import format_date

from dateutil.relativedelta import relativedelta
from itertools import chain
_logger = getLogger(__name__)

class ReportAccountAgedPartnerInherit(models.AbstractModel):
    _inherit='account.aged.partner'

    invoice_date = fields.Date(string='Inv. Date')

    currency_name = fields.Char(string="Currency")
    
    currency_rate = fields.Char('Currency Rate', compute='_get_rate')
    
    price_total = fields.Char(string='Price Total')
    
    origin_price_total = fields.Char(string='Original Currency Total', compute='_get_currency_total')
    
    def _get_rate(self):
        for rec in self:
            rec.currency_rate = ''
            dateinvoice = rec.invoice_date
            if dateinvoice:
                if rec.currency_name == 'USD':
                    currencyrate = rec.move_id._get_rates_currency(dateinvoice)
                    rec.currency_rate = round((1 / currencyrate.get('USD')),6)
                elif rec.currency_name == 'MXN':
                    rec.currency_rate = 1
    
    def _get_currency_total(self):
        for rec in self:
            if rec.price_total == '$ .00':
                rec.origin_price_total = ''
            else:
                rec.origin_price_total = rec.price_total
            

    @api.model
    def _get_sql(self):
        options = self.env.context['report_options']
        query = ("""
            SELECT
                {move_line_fields},
                account_move_line.partner_id AS partner_id,
                partner.name AS partner_name,
                COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                account_move_line.payment_id AS payment_id,
                COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                account_move_line.expected_pay_date AS expected_pay_date,
                move.invoice_date AS invoice_date,
                '$ ' || to_char(abs(account_move_line.price_total),'FM999G999D00') as price_total,
                res_currency.name AS currency_name,
                move.move_type AS move_type,
                move.name AS move_name,
                journal.code AS journal_code,
                COALESCE(NULLIF(account_tr.value, ''), account.name) as account_name,
                account.code AS account_code,""" + ','.join([("""
                CASE WHEN period_table.period_index = {i}
                THEN %(sign)s * ROUND((
                    account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                ) * currency_table.rate, currency_table.precision)
                ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
            FROM account_move_line
            JOIN account_move move ON account_move_line.move_id = move.id
            JOIN account_journal journal ON journal.id = account_move_line.journal_id
            JOIN account_account account ON account.id = account_move_line.account_id
            LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
            LEFT JOIN ir_property trust_property ON (
                trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                AND trust_property.name = 'trust'
                AND trust_property.company_id = account_move_line.company_id
            )
            JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
            JOIN res_currency ON res_currency.id = COALESCE(account_move_line.currency_id, journal.currency_id)
            LEFT JOIN LATERAL (
                SELECT part.amount, part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date)s
            ) part_debit ON part_debit.debit_move_id = account_move_line.id
            LEFT JOIN LATERAL (
                SELECT part.amount, part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date)s
            ) part_credit ON part_credit.credit_move_id = account_move_line.id
            JOIN {period_table} ON (
                period_table.date_start IS NULL
                OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
            )
            AND (
                period_table.date_stop IS NULL
                OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
            )
            LEFT JOIN ir_translation account_tr ON (
                account_tr.name = 'account.account,name'
                AND account_tr.res_id = account.id
                AND account_tr.type = 'model'
                AND account_tr.lang = %(lang)s
            )
            WHERE account.internal_type = %(account_type)s
            GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                period_table.period_index, currency_table.rate, res_currency.name, currency_table.precision, account_name
            HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
        """).format(
            move_line_fields=self._get_move_line_fields('account_move_line'),
            currency_table=self.env['res.currency']._get_query_currency_table(options),
            period_table=self._get_query_period_table(options),
        )
        params = {
            'account_type': options['filter_account_type'],
            'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
            'date': options['date']['date_to'],
            'lang': self.env.user.lang or get_lang(self.env).code,
        }
        return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)

        
    @api.model
    def _get_column_details(self, options):
        return [
            self._header_column(),
            self.with_context(no_format=False)._field_column('report_date'),
            self._field_column('journal_code', name=_("Journal")),
            self._field_column('account_name', name=_("Account")),
            self.with_context(no_format=False)._field_column('expected_pay_date'),
            self._field_column('invoice_date'),
            self._field_column('currency_rate'),
            self._field_column('origin_price_total'),
            self._field_column('currency_name'),
            self._field_column('period0', name=_("As of: %s") % format_date(self.env, options['date']['date_to'])),
            self._field_column('period1', sortable=True),
            self._field_column('period2', sortable=True),
            self._field_column('period3', sortable=True),
            self._field_column('period4', sortable=True),
            self._field_column('period5', sortable=True),
            self._custom_column(  # Avoid doing twice the sub-select in the view
                name=_('Total'),
                classes=['number'],
                formatter=self.format_value,
                getter=(lambda v: v['period0'] + v['period1'] + v['period2'] + v['period3'] + v['period4'] + v['period5']),
                sortable=True,
            ),
        ]