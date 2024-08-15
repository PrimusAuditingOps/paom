from odoo import api, exceptions, fields, models, _
from logging import getLogger
from odoo.tools.misc import format_date

from dateutil.relativedelta import relativedelta
from itertools import chain
_logger = getLogger(__name__)

class ReportAgedReceivableCustom(models.AbstractModel):
    
    _inherit='account.aged.partner.balance.report.handler'
    
    def _get_rate(self, invoice_date, currency_name, move_id):
        move = self.env['account.move'].browse(move_id)
        if invoice_date:
            if currency_name == 'USD':
                currencyrate = move._get_rates_currency(invoice_date)
                return round((1 / currencyrate.get('USD')),6)
            elif currency_name == 'MXN':
                return 1
                
        return ''
    
    @api.model
    def _prepare_partner_values(self):
        result = super(ReportAgedReceivableCustom, self)._prepare_partner_values()
        result.update({'currency_rate': None})
        
        return result
    
    @api.model
    def _aged_partner_report_custom_engine_common(self, options, internal_type, current_groupby, next_groupby, offset=0, limit=None):
        report = self.env['account.report'].browse(options['report_id'])
        report._check_groupby_fields((next_groupby.split(',') if next_groupby else []) + ([current_groupby] if current_groupby else []))

        def minus_days(date_obj, days):
            return fields.Date.to_string(date_obj - relativedelta(days=days))

        date_to = fields.Date.from_string(options['date']['date_to'])
        periods = [
            (False, fields.Date.to_string(date_to)),
            (minus_days(date_to, 1), minus_days(date_to, 30)),
            (minus_days(date_to, 31), minus_days(date_to, 60)),
            (minus_days(date_to, 61), minus_days(date_to, 90)),
            (minus_days(date_to, 91), minus_days(date_to, 120)),
            (minus_days(date_to, 121), False),
        ]

        def build_result_dict(report, query_res_lines):
            rslt = {f'period{i}': 0 for i in range(len(periods))}

            for query_res in query_res_lines:
                for i in range(len(periods)):
                    period_key = f'period{i}'
                    rslt[period_key] += query_res[period_key]
                    

            if current_groupby == 'id':
                query_res = query_res_lines[0] # We're grouping by id, so there is only 1 element in query_res_lines anyway
                currency = self.env['res.currency'].browse(query_res['currency_id'][0]) if len(query_res['currency_id']) == 1 else None
                expected_date = len(query_res['expected_date']) == 1 and query_res['expected_date'][0] or len(query_res['due_date']) == 1 and query_res['due_date'][0]
                rslt.update({
                    'invoice_date': query_res['invoice_date'][0] if len(query_res['invoice_date']) == 1 else None,
                    'due_date': query_res['due_date'][0] if len(query_res['due_date']) == 1 else None,
                    'amount_currency': query_res['amount_currency'],
                    'currency_id': query_res['currency_id'][0] if len(query_res['currency_id']) == 1 else None,
                    'currency': currency.display_name if currency else None,
                    'account_name': query_res['account_name'][0] if len(query_res['account_name']) == 1 else None,
                    'expected_date': expected_date or None,
                    'total': None,
                    'has_sublines': query_res['aml_count'] > 0,

                    # Needed by the custom_unfold_all_batch_data_generator, to speed-up unfold_all
                    'partner_id': query_res['partner_id'][0] if query_res['partner_id'] else None,
                })
                
                rslt.update({'currency_rate': self._get_rate(rslt.get('invoice_date'), rslt.get('currency'), query_res['move_id'][0])})
                
            else:
                rslt.update({
                    'invoice_date': None,
                    'due_date': None,
                    'amount_currency': None,
                    'currency_id': None,
                    'currency': None,
                    'currency_rate': None,
                    'account_name': None,
                    'expected_date': None,
                    'total': sum(rslt[f'period{i}'] for i in range(len(periods))),
                    'has_sublines': False,
                })
                
            

            return rslt

        # Build period table
        period_table_format = ('(VALUES %s)' % ','.join("(%s, %s, %s)" for period in periods))
        params = list(chain.from_iterable(
            (period[0] or None, period[1] or None, i)
            for i, period in enumerate(periods)
        ))
        period_table = self.env.cr.mogrify(period_table_format, params).decode(self.env.cr.connection.encoding)

        # Build query
        tables, where_clause, where_params = report._query_get(options, 'strict_range', domain=[('account_id.account_type', '=', internal_type)])

        currency_table = report._get_query_currency_table(options)
        always_present_groupby = "period_table.period_index, currency_table.rate, currency_table.precision"
        if current_groupby:
            select_from_groupby = f"account_move_line.{current_groupby} AS grouping_key,"
            groupby_clause = f"account_move_line.{current_groupby}, {always_present_groupby}"
        else:
            select_from_groupby = ''
            groupby_clause = always_present_groupby
        select_period_query = ','.join(
            f"""
                CASE WHEN period_table.period_index = {i}
                THEN %s * (
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision))
                    - COALESCE(SUM(ROUND(part_debit.amount * currency_table.rate, currency_table.precision)), 0)
                    + COALESCE(SUM(ROUND(part_credit.amount * currency_table.rate, currency_table.precision)), 0)
                )
                ELSE 0 END AS period{i}
            """
            for i in range(len(periods))
        )

        tail_query, tail_params = report._get_engine_query_tail(offset, limit)
        query = f"""
            WITH period_table(date_start, date_stop, period_index) AS ({period_table})

            SELECT
                {select_from_groupby}
                %s * (
                    SUM(account_move_line.amount_currency)
                    - COALESCE(SUM(part_debit.debit_amount_currency), 0)
                    + COALESCE(SUM(part_credit.credit_amount_currency), 0)
                ) AS amount_currency,
                ARRAY_AGG(DISTINCT move.id) AS move_id,
                ARRAY_AGG(DISTINCT account_move_line.partner_id) AS partner_id,
                ARRAY_AGG(account_move_line.payment_id) AS payment_id,
                ARRAY_AGG(DISTINCT move.invoice_date) AS invoice_date,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.date_maturity, account_move_line.date)) AS report_date,
                ARRAY_AGG(DISTINCT account_move_line.expected_pay_date) AS expected_date,
                ARRAY_AGG(DISTINCT account.code) AS account_name,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.date_maturity, account_move_line.date)) AS due_date,
                ARRAY_AGG(DISTINCT account_move_line.currency_id) AS currency_id,
                COUNT(account_move_line.id) AS aml_count,
                ARRAY_AGG(account.code) AS account_code,
                {select_period_query}

            FROM {tables}

            JOIN account_journal journal ON journal.id = account_move_line.journal_id
            JOIN account_account account ON account.id = account_move_line.account_id
            JOIN account_move move ON move.id = account_move_line.move_id
            JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id

            LEFT JOIN LATERAL (
                SELECT
                    SUM(part.amount) AS amount,
                    SUM(part.debit_amount_currency) AS debit_amount_currency,
                    part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %s
                GROUP BY part.debit_move_id
            ) part_debit ON part_debit.debit_move_id = account_move_line.id

            LEFT JOIN LATERAL (
                SELECT
                    SUM(part.amount) AS amount,
                    SUM(part.credit_amount_currency) AS credit_amount_currency,
                    part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %s
                GROUP BY part.credit_move_id
            ) part_credit ON part_credit.credit_move_id = account_move_line.id

            JOIN period_table ON
                (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND
                (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                )

            WHERE {where_clause}

            GROUP BY {groupby_clause}

            HAVING
                (
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))
                    - COALESCE(SUM(ROUND(part_debit.amount * currency_table.rate, currency_table.precision)), 0)
                ) != 0
                OR
                (
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))
                    - COALESCE(SUM(ROUND(part_credit.amount * currency_table.rate, currency_table.precision)), 0)
                ) != 0
            {tail_query}
        """

        multiplicator = -1 if internal_type == 'liability_payable' else 1
        params = [
            multiplicator,
            *([multiplicator] * len(periods)),
            date_to,
            date_to,
            *where_params,
            *tail_params,
        ]
        self._cr.execute(query, params)
        query_res_lines = self._cr.dictfetchall()

        if not current_groupby:
            return build_result_dict(report, query_res_lines)
        else:
            rslt = []

            all_res_per_grouping_key = {}
            for query_res in query_res_lines:
                grouping_key = query_res['grouping_key']
                all_res_per_grouping_key.setdefault(grouping_key, []).append(query_res)

            for grouping_key, query_res_lines in all_res_per_grouping_key.items():
                rslt.append((grouping_key, build_result_dict(report, query_res_lines)))

            return rslt



# class ReportAccountAgedPartnerInherit(models.AbstractModel):
#     _inherit='account.aged.partner'

#     invoice_date = fields.Date(string='Inv. Date')

#     currency_name = fields.Char(string="Currency")
    
#     currency_rate = fields.Char('Currency Rate', compute='_get_rate')
    
#     price_total = fields.Char(string='Price Total')
    
#     origin_price_total = fields.Char(string='Original Currency Total', compute='_get_currency_total')
    
#     amount_residual = fields.Float(string="Amount Due")
    
#     def _get_rate(self):
#         for rec in self:
#             rec.currency_rate = ''
#             dateinvoice = rec.invoice_date
#             if dateinvoice:
#                 if rec.currency_name == 'USD':
#                     currencyrate = rec.move_id._get_rates_currency(dateinvoice)
#                     rec.currency_rate = round((1 / currencyrate.get('USD')),6)
#                 elif rec.currency_name == 'MXN':
#                     rec.currency_rate = 1
    
#     def _get_currency_total(self):
#         for rec in self:
            
#             if rec.amount_residual <= 0:
#                 if rec.price_total == '$ .00':
#                     rec.origin_price_total = ''
#                 else:
#                     rec.origin_price_total = rec.price_total
#             else:
#                 rec.origin_price_total = '$ {:.2f}'.format(rec.amount_residual)
            

#     @api.model
#     def _get_sql(self):
#         options = self.env.context['report_options']
#         query = ("""
#             SELECT
#                 {move_line_fields},
#                 account_move_line.partner_id AS partner_id,
#                 partner.name AS partner_name,
#                 COALESCE(trust_property.value_text, 'normal') AS partner_trust,
#                 COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
#                 account_move_line.payment_id AS payment_id,
#                 COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
#                 account_move_line.expected_pay_date AS expected_pay_date,
#                 move.invoice_date AS invoice_date,
#                 '$ ' || to_char(abs(account_move_line.price_total),'FM999G999D00') as price_total,
#                 move.amount_residual as amount_residual,
#                 res_currency.name AS currency_name,
#                 move.move_type AS move_type,
#                 move.name AS move_name,
#                 journal.code AS journal_code,
#                 COALESCE(NULLIF(account_tr.value, ''), account.name) as account_name,
#                 account.code AS account_code,""" + ','.join([("""
#                 CASE WHEN period_table.period_index = {i}
#                 THEN %(sign)s * ROUND((
#                     account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
#                 ) * currency_table.rate, currency_table.precision)
#                 ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
#             FROM account_move_line
#             JOIN account_move move ON account_move_line.move_id = move.id
#             JOIN account_journal journal ON journal.id = account_move_line.journal_id
#             JOIN account_account account ON account.id = account_move_line.account_id
#             LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
#             LEFT JOIN ir_property trust_property ON (
#                 trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
#                 AND trust_property.name = 'trust'
#                 AND trust_property.company_id = account_move_line.company_id
#             )
#             JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
#             JOIN res_currency ON res_currency.id = COALESCE(account_move_line.currency_id, journal.currency_id)
#             LEFT JOIN LATERAL (
#                 SELECT part.amount, part.debit_move_id
#                 FROM account_partial_reconcile part
#                 WHERE part.max_date <= %(date)s
#             ) part_debit ON part_debit.debit_move_id = account_move_line.id
#             LEFT JOIN LATERAL (
#                 SELECT part.amount, part.credit_move_id
#                 FROM account_partial_reconcile part
#                 WHERE part.max_date <= %(date)s
#             ) part_credit ON part_credit.credit_move_id = account_move_line.id
#             JOIN {period_table} ON (
#                 period_table.date_start IS NULL
#                 OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
#             )
#             AND (
#                 period_table.date_stop IS NULL
#                 OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
#             )
#             LEFT JOIN ir_translation account_tr ON (
#                 account_tr.name = 'account.account,name'
#                 AND account_tr.res_id = account.id
#                 AND account_tr.type = 'model'
#                 AND account_tr.lang = %(lang)s
#             )
#             WHERE account.internal_type = %(account_type)s
#             GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
#                 period_table.period_index, currency_table.rate, res_currency.name, currency_table.precision, account_name
#             HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
#         """).format(
#             move_line_fields=self._get_move_line_fields('account_move_line'),
#             currency_table=self.env['res.currency']._get_query_currency_table(options),
#             period_table=self._get_query_period_table(options),
#         )
#         params = {
#             'account_type': options['filter_account_type'],
#             'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
#             'date': options['date']['date_to'],
#             'lang': self.env.user.lang or get_lang(self.env).code,
#         }
#         return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)

        
#     @api.model
#     def _get_column_details(self, options):
#         return [
#             self._header_column(),
#             self.with_context(no_format=False)._field_column('report_date'),
#             self._field_column('journal_code', name=_("Journal")),
#             self._field_column('account_name', name=_("Account")),
#             self.with_context(no_format=False)._field_column('expected_pay_date'),
#             self._field_column('invoice_date'),
#             self._field_column('currency_rate'),
#             self._field_column('origin_price_total'),
#             self._field_column('currency_name'),
#             self._field_column('period0', name=_("As of: %s") % format_date(self.env, options['date']['date_to'])),
#             self._field_column('period1', sortable=True),
#             self._field_column('period2', sortable=True),
#             self._field_column('period3', sortable=True),
#             self._field_column('period4', sortable=True),
#             self._field_column('period5', sortable=True),
#             self._custom_column(  # Avoid doing twice the sub-select in the view
#                 name=_('Total'),
#                 classes=['number'],
#                 formatter=self.format_value,
#                 getter=(lambda v: v['period0'] + v['period1'] + v['period2'] + v['period3'] + v['period4'] + v['period5']),
#                 sortable=True,
#             ),
#         ]
