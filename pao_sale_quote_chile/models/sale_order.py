# -*- coding: utf-8 -*-
import re
from string import ascii_lowercase

from babel.dates import format_date as babel_format_date
from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, is_html_empty
from odoo.tools.image import image_data_uri
from odoo.tools.misc import babel_locale_parse

# Label printed below the price column of a table that has a single currency.
CURRENCY_HEADER_LABELS = {'USD': 'USD $', 'EUR': 'EUR €', 'GBP': 'GBP £'}
# Prefix printed before each amount of a table that mixes currencies.
CURRENCY_CELL_LABELS = {'USD': 'USD', 'EUR': '€', 'GBP': '£'}

FEMALE_TITLES = {'señora', 'señorita', 'sra', 'srta', 'madam', 'miss', 'mrs', 'ms'}
MALE_TITLES = {'señor', 'sr', 'mister', 'mr', 'sir'}

# Inline styles of the generated tables: the format is edited in the HTML editor, so it cannot rely on CSS classes.
STYLE_TITLE = 'font-weight: bold; margin: 14px 0 6px 20px;'
STYLE_TABLE = 'width: 100%; border-collapse: collapse; border: 2px solid #000000;'
STYLE_TH = ('border: 1px solid #000000; padding: 4px 8px; background-color: #8c8c8c; '
            'text-align: center; font-weight: bold;')
STYLE_TD = 'border: 1px solid #000000; padding: 4px 8px;'
STYLE_TD_PRICE = 'border: 1px solid #000000; padding: 4px 8px; text-align: center; width: 26%;'
STYLE_TD_FOOTER = ('border: 1px solid #000000; padding: 4px 8px; background-color: #bfbfbf; '
                   'text-align: center; font-weight: bold;')

TABLES_PLACEHOLDER = '[[TABLAS]]'
SIGNATURE_PLACEHOLDER = '[[FIRMA]]'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pao_use_chile_format = fields.Boolean(
        string='Chile Quotation Format',
        compute='_compute_pao_use_chile_format',
    )
    pao_quote_format = fields.Html(
        string='Quotation Format',
        copy=False,
        help="Content printed in the quotation (between the logo header and the footer). "
             "Generated from the quotation template and the order lines, then freely editable.",
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
            for table in order._pao_quote_tables():
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
    # CRUD: the format is generated automatically while it is empty
    # ------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._pao_generate_empty_quote_format()
        return orders

    def write(self, vals):
        res = super().write(vals)
        if 'sale_order_template_id' in vals:
            self._pao_generate_empty_quote_format()
        return res

    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------

    def action_pao_generate_quote_format(self):
        self._pao_generate_quote_format()
        return True

    # ------------------------------------------------------------
    # Native hooks
    # ------------------------------------------------------------

    def _get_name_portal_content_view(self):
        if self.pao_use_chile_format:
            return 'pao_sale_quote_chile.sale_order_portal_content_chile'
        return super()._get_name_portal_content_view()

    # ------------------------------------------------------------
    # Format generation
    # ------------------------------------------------------------

    def _pao_get_quote_config(self):
        self.ensure_one()
        return self.env['pao.quote.config'].sudo().search([('company_id', '=', self.company_id.id)], limit=1)

    def _pao_generate_empty_quote_format(self):
        self.filtered(
            lambda order: order.pao_use_chile_format and is_html_empty(order.pao_quote_format)
        )._pao_generate_quote_format()

    def _pao_generate_quote_format(self):
        for order in self.filtered('pao_use_chile_format'):
            order.pao_quote_format = order._pao_build_quote_format()

    def _pao_quote_format_template(self):
        """Design of the format: the one of the quotation template, else the default of the company."""
        self.ensure_one()
        template = self.sale_order_template_id.pao_quote_format_template
        if is_html_empty(template):
            template = self._pao_get_quote_config().default_format_template
        return template or ''

    def _pao_build_quote_format(self):
        """Format template with its placeholders replaced by the data of the order."""
        self.ensure_one()
        order = self.with_context(lang=self._pao_quote_lang())
        contact = order._pao_quote_contact()
        partner = contact or order.partner_id
        values = {
            '[[NUMERO]]': order.name if (order.name or '').startswith('#') else f'#{order.name}',
            '[[CLIENTE]]': order.partner_id.commercial_partner_id.name or '',
            '[[CONTACTO]]': contact.name or '',
            '[[EMAIL]]': partner.email or '',
            '[[TELEFONO]]': partner.phone or partner.mobile or 'No Registra.',
            '[[FECHA]]': order._pao_quote_date_label(),
            '[[SALUDO]]': order._pao_quote_greeting(),
        }
        html = str(order._pao_quote_format_template())
        for placeholder, value in values.items():
            html = html.replace(placeholder, str(escape(value)))
        tables = str(order._pao_quote_tables_html())
        # A table cannot live inside the paragraph the editor wraps the placeholder in.
        html = re.sub(r'<p[^>]*>\s*' + re.escape(TABLES_PLACEHOLDER) + r'\s*</p>', lambda m: tables, html)
        html = html.replace(TABLES_PLACEHOLDER, tables)
        return Markup(html)

    def _pao_render_quote_format(self):
        """Printable content: the saved format (built on the fly when empty) with the signature image."""
        self.ensure_one()
        html = self.pao_quote_format
        if is_html_empty(html):
            html = self._pao_build_quote_format()
        signature = self._pao_get_quote_config().signature_image
        image = (
            str(Markup('<img src="%s" style="max-height: 90px;" alt="Firma"/>') % image_data_uri(signature))
            if signature else ''
        )
        return Markup(str(html).replace(SIGNATURE_PLACEHOLDER, image))

    # ------------------------------------------------------------
    # Placeholder values
    # ------------------------------------------------------------

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

    def _pao_format_amount(self, amount, currency):
        """1850 -> '1.850', 50.5 -> '50,50' (Chilean separators, decimals only when needed)."""
        amount = currency.round(amount)
        digits = 0 if float_is_zero(amount - round(amount), precision_digits=currency.decimal_places) else currency.decimal_places
        text = f'{amount:,.{digits}f}'
        return text.replace(',', '\x00').replace('.', ',').replace('\x00', '.')

    # ------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------

    def _pao_quote_tables(self):
        """Tables of the quotation built from the order lines.

        Each native section starts a table; note lines become paragraphs before the table (no rows yet) or
        footer rows after them; product lines are rows, and a line marked 'Combine' joins the previous row.

        :return: list of {'title', 'notes_before', 'footers', 'rows': [{'names', 'amount', 'currencies'}]}
        """
        self.ensure_one()
        tables = []
        table = None
        for line in self.order_line:
            if line.is_downpayment:
                continue
            if line.display_type == 'line_section':
                table = {'title': line.name, 'notes_before': [], 'footers': [], 'rows': []}
                tables.append(table)
                continue
            if table is None:
                table = {'title': False, 'notes_before': [], 'footers': [], 'rows': []}
                tables.append(table)
            if line.display_type == 'line_note':
                (table['footers'] if table['rows'] else table['notes_before']).append(line.name or '')
                continue
            currency = line._pao_quote_currency()
            if line.pao_quote_combine and table['rows']:
                row = table['rows'][-1]
                row['names'].append(line.name or '')
                row['amount'] += line.price_subtotal
                row['currencies'] |= currency
            else:
                table['rows'].append({
                    'names': [line.name or ''],
                    'amount': line.price_subtotal,
                    'currencies': currency,
                })
        return tables

    def _pao_quote_tables_html(self):
        """HTML of the tables, with inline styles so the user can keep editing them."""
        self.ensure_one()
        letters = iter(ascii_lowercase)
        parts = []
        for table in self._pao_quote_tables():
            if table['title']:
                letter = next(letters, '')
                title = f'{letter}. {table["title"]}' if letter else table['title']
                parts.append(Markup('<p style="%s">%s</p>') % (STYLE_TITLE, title))
            for note in table['notes_before']:
                parts.append(Markup('<p>%s</p>') % self._pao_multiline(note))
            if not table['rows']:
                continue

            currencies = self.env['res.currency']
            for row in table['rows']:
                currencies |= row['currencies']
            single_currency = currencies if len(currencies) == 1 else False
            price_header = Markup('Valor')
            if single_currency:
                label = CURRENCY_HEADER_LABELS.get(single_currency.name, f'{single_currency.name} {single_currency.symbol}')
                price_header = Markup('Valor<br/>%s') % label

            rows = [Markup('<tr><th style="%s">ALTERNATIVAS</th><th style="%s">%s</th></tr>') % (
                STYLE_TH, STYLE_TH, price_header)]
            for row in table['rows']:
                name = Markup(' + ').join(self._pao_multiline(row_name) for row_name in row['names'])
                rows.append(Markup('<tr><td style="%s">%s</td><td style="%s">%s</td></tr>') % (
                    STYLE_TD, name, STYLE_TD_PRICE, self._pao_row_amount(row, single_currency)))
            for footer in table['footers']:
                rows.append(Markup('<tr><td colspan="2" style="%s">%s</td></tr>') % (
                    STYLE_TD_FOOTER, self._pao_multiline(footer)))
            parts.append(Markup('<table style="%s"><tbody>%s</tbody></table><p><br/></p>') % (
                STYLE_TABLE, Markup('').join(rows)))
        return Markup('').join(parts)

    def _pao_row_amount(self, row, single_currency):
        if len(row['currencies']) != 1:
            return '-'
        amount = self._pao_format_amount(row['amount'], row['currencies'])
        if single_currency:
            return amount
        prefix = CURRENCY_CELL_LABELS.get(row['currencies'].name, row['currencies'].symbol)
        return f'{prefix} {amount}'

    def _pao_multiline(self, text):
        return Markup('<br/>').join(escape(part) for part in (text or '').split('\n'))
