# -*- coding: utf-8 -*-
from string import ascii_lowercase

from babel.dates import format_date as babel_format_date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, is_html_empty
from odoo.tools.misc import babel_locale_parse

# Label printed below the price column of a table that has a single currency.
CURRENCY_HEADER_LABELS = {'USD': 'USD $', 'EUR': 'EUR €', 'GBP': 'GBP £'}
# Prefix printed before each amount of a table that mixes currencies.
CURRENCY_CELL_LABELS = {'USD': 'USD', 'EUR': '€', 'GBP': '£'}

FEMALE_TITLES = {'señora', 'señorita', 'sra', 'srta', 'madam', 'miss', 'mrs', 'ms'}
MALE_TITLES = {'señor', 'sr', 'mister', 'mr', 'sir'}


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pao_use_chile_format = fields.Boolean(
        string='Chile Quotation Format',
        compute='_compute_pao_use_chile_format',
    )

    @api.depends('company_id')
    def _compute_pao_use_chile_format(self):
        configs = self.env['pao.quote.config'].sudo().search([('company_id', 'in', self.company_id.ids)])
        companies = configs.company_id
        for order in self:
            order.pao_use_chile_format = order.company_id in companies

    @api.constrains('order_line')
    def _check_pao_quote_combined_currency(self):
        for order in self.filtered('pao_use_chile_format'):
            for group in order._pao_quote_groups()['groups']:
                for table in group['tables']:
                    for row in table['rows']:
                        if len(row['currencies']) > 1:
                            raise ValidationError(_(
                                "The lines '%(lines)s' are combined in a single row of the quotation but their "
                                "products have different base currencies (%(currencies)s). Uncheck 'Combine' "
                                "on the line or use products with the same base currency.",
                                lines=' + '.join(row['names']),
                                currencies=', '.join(row['currencies'].mapped('name')),
                            ))

    # ------------------------------------------------------------
    # Native hooks
    # ------------------------------------------------------------

    def _get_name_portal_content_view(self):
        if self._pao_is_chile_quote():
            return 'pao_sale_quote_chile.sale_order_portal_content_chile'
        return super()._get_name_portal_content_view()

    # ------------------------------------------------------------
    # Chile quotation helpers (used by the report and portal templates)
    # ------------------------------------------------------------

    def _pao_get_quote_config(self):
        self.ensure_one()
        return self.env['pao.quote.config'].sudo().search([('company_id', '=', self.company_id.id)], limit=1)

    def _pao_is_chile_quote(self):
        """The regional format only applies to quotations, confirmed orders keep the native report."""
        self.ensure_one()
        return self.state in ('draft', 'sent') and self.pao_use_chile_format

    def _pao_quote_lang(self):
        lang = self._get_lang()
        return lang if lang and lang.startswith('es') else 'es_CL'

    def _pao_quote_date_label(self):
        """'Septiembre 2026.'"""
        self.ensure_one()
        if not self.date_order:
            return ''
        label = babel_format_date(
            self.date_order.date(), format='MMMM y', locale=babel_locale_parse(self._pao_quote_lang()),
        )
        return label[:1].upper() + label[1:] + '.'

    def _pao_quote_contact(self):
        """Contact person of the quotation, empty when the customer itself is the order partner."""
        self.ensure_one()
        partner = self.partner_id
        return partner if partner != partner.commercial_partner_id and not partner.is_company else partner.browse()

    def _pao_quote_greeting(self):
        """'Estimada Karina:' using the contact title, never guessing from the name."""
        self.ensure_one()
        contact = self._pao_quote_contact()
        if not contact:
            return 'Estimados:'
        titles = {
            (value or '').strip().lower().rstrip('.')
            for value in (contact.title.shortcut, contact.title.name)
        }
        if titles & FEMALE_TITLES:
            word = 'Estimada'
        elif titles & MALE_TITLES:
            word = 'Estimado'
        else:
            word = 'Estimado/a'
        first_name = (contact.name or '').split()[0] if contact.name else ''
        return f'{word} {first_name}:' if first_name else f'{word}:'

    def _pao_is_foreign_customer(self):
        self.ensure_one()
        partner_country = self.partner_id.commercial_partner_id.country_id
        company_country = self.company_id.country_id
        return bool(partner_country and company_country and partner_country != company_country)

    def _pao_quote_schemes(self):
        self.ensure_one()
        lines = self.order_line.filtered(lambda l: not l.display_type)
        return lines.product_id.product_tmpl_id.pao_quote_scheme_id

    def _pao_quote_intro(self):
        self.ensure_one()
        config = self._pao_get_quote_config()
        if any(self._pao_quote_schemes().mapped('use_long_intro')) or not config.intro_short:
            return config.intro_long
        return config.intro_short

    def _pao_quote_blocks(self, position):
        """Information blocks of a position, filtered by the schemes of the quotation and the customer country."""
        self.ensure_one()
        schemes = self._pao_quote_schemes()
        foreign = self._pao_is_foreign_customer()
        blocks = self.env['pao.quote.block'].sudo().search([
            ('position', '=', position),
            ('company_id', 'in', [False, self.company_id.id]),
        ])
        return blocks.filtered(
            lambda block: (block.apply_always or block.scheme_ids & schemes)
            and (block.audience == 'all' or (block.audience == 'foreign') == foreign)
        )

    def _pao_format_amount(self, amount, currency):
        """1850 -> '1.850', 50.5 -> '50,50' (Chilean separators, decimals only when needed)."""
        amount = currency.round(amount)
        digits = 0 if float_is_zero(amount - round(amount), precision_digits=currency.decimal_places) else currency.decimal_places
        text = f'{amount:,.{digits}f}'
        return text.replace(',', '\x00').replace('.', ',').replace('\x00', '.')

    def _pao_quote_groups(self):
        """Structure of the quotation body.

        Each native section starts a table; note lines become paragraphs before (no rows yet) or after the
        table; product lines are rows, and a line marked 'Combine' joins the previous row. Consecutive tables
        sharing the category of their format are grouped under one numbered heading.

        :return: {'groups': [{'category', 'number', 'tables': [table dict]}], 'billing_number': int or False}
        """
        self.ensure_one()
        tables = []
        table = None
        for line in self.order_line:
            if line.is_downpayment:
                continue
            if line.display_type == 'line_section':
                table = self._pao_new_quote_table(line.name)
                tables.append(table)
                continue
            if table is None:
                table = self._pao_new_quote_table(False)
                tables.append(table)
            if line.display_type == 'line_note':
                (table['notes_after'] if table['rows'] else table['notes_before']).append(line.name or '')
                continue
            if not table['format'] and line.pao_quote_table_id:
                table['format'] = line.pao_quote_table_id
            currency = line._pao_quote_currency()
            if line.pao_quote_combine and table['rows']:
                row = table['rows'][-1]
                row['names'].append(line.name or '')
                row['lines'] |= line
                row['amount'] += line.price_subtotal
                row['currencies'] |= currency
            else:
                table['rows'].append({
                    'names': [line.name or ''],
                    'lines': line,
                    'amount': line.price_subtotal,
                    'currencies': currency,
                })

        for table in tables:
            self._pao_finish_quote_table(table)

        groups = []
        for table in tables:
            category = table['format'].category_id
            if groups and groups[-1]['category'] == category:
                groups[-1]['tables'].append(table)
            else:
                groups.append({'category': category, 'number': False, 'tables': [table]})

        number = 0
        for group in groups:
            if group['category']:
                number += 1
                group['number'] = number
            letters = iter(ascii_lowercase)
            for table in group['tables']:
                table['letter'] = next(letters, '') if table['title'] else ''
        return {'groups': groups, 'billing_number': number + 1 if number else False}

    def _pao_new_quote_table(self, title):
        return {
            'title': title,
            'letter': '',
            'format': self.env['pao.quote.table'],
            'notes_before': [],
            'notes_after': [],
            'rows': [],
        }

    def _pao_finish_quote_table(self, table):
        """Add printable amounts, currency labels, footnotes and total to a table dict."""
        currencies = self.env['res.currency']
        for row in table['rows']:
            currencies |= row['currencies']
        single_currency = currencies if len(currencies) == 1 else False
        table['currency_label'] = (
            CURRENCY_HEADER_LABELS.get(single_currency.name, f'{single_currency.name} {single_currency.symbol}')
            if single_currency else ''
        )
        for row in table['rows']:
            if len(row['currencies']) != 1:
                row['amount_label'] = '-'
                continue
            amount = self._pao_format_amount(row['amount'], row['currencies'])
            if not single_currency:
                prefix = CURRENCY_CELL_LABELS.get(row['currencies'].name, row['currencies'].symbol)
                amount = f'{prefix} {amount}'
            row['amount_label'] = amount

        table_format = table['format']
        notes = [table_format.notes] if not is_html_empty(table_format.notes) else []
        seen = self.env['product.template']
        for row in table['rows']:
            for template in row['lines'].product_id.product_tmpl_id:
                if template not in seen and not is_html_empty(template.pao_quote_note):
                    notes.append(template.pao_quote_note)
                seen |= template
        if not is_html_empty(table_format.notes_after):
            notes.append(table_format.notes_after)
        table['footnotes'] = notes

        table['total_label'] = ''
        if table['format'].show_total and single_currency and table['rows']:
            total = sum(row['amount'] for row in table['rows'])
            table['total_label'] = self._pao_format_amount(total, single_currency)
