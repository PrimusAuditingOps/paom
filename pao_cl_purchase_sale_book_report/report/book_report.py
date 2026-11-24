import re
from collections import defaultdict

from odoo import api, models
from odoo.exceptions import UserError

MONTHS = [
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO',
    'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
]

# Kind of document, taken from the start of the invoice number (FACEE/2026/10/0001,
# FACEL/2026/10/0060, BHE 0001...):
#   code   -> shown in DOCUMENTO and in RESUMEN
#   label  -> RESUMEN line
#   exempt -> True: the whole total goes to M. EXENTO (and TOTAL);
#             False: subtotal to M. AFECTO, taxes to I.V.A., subtotal + taxes to TOTAL.
KINDS = {
    'FACEE': {'code': 'FAC-EE', 'label': 'FACTURAS ELECT. EXENTAS', 'exempt': True},
    'FACEL': {'code': 'FAC-EL', 'label': 'FACTURAS ELECT.', 'exempt': False},
    'BHE': {'code': 'BHE', 'label': 'BOLETAS DE HONORARIOS ELECT.', 'exempt': False},
}
# Fallback when the number has none of those prefixes: Chilean (SII) document type code.
DOCUMENT_TYPE_KINDS = {'34': 'FACEE', '33': 'FACEL', '71': 'BHE'}

# Boletas de honorarios (electronic and paper): included in the book as M. AFECTO
# (decided with the user). Set to False to leave them out.
INCLUDE_FEE_SLIPS = True
FEE_SLIP_CODES = {'70', '71'}

# Sales book: M. EXENTO / M. AFECTO by Chilean (SII) document type code.
#   Credit notes: exempt 112, taxed 61.
#   Invoices:     exempt 34, 41, 110, 111; taxed 33, 56, 39, 71, 46.
SALE_EXEMPT_CODES = {'112', '34', '41', '110', '111'}
SALE_TAXED_CODES = {'61', '33', '56', '39', '71', '46'}

# Rows that fit on a page: the first page has no "TOTAL ANTERIOR" row.
ROWS_FIRST_PAGE = 34
ROWS_OTHER_PAGES = 33

AMOUNT_KEYS = ('exempt', 'taxed', 'tax', 'total')


class PurchaseBookReport(models.AbstractModel):
    _name = 'report.pao_cl_purchase_sale_book_report.report_purchase_book'
    _description = 'Reporte: Libro de compras (Chile)'

    # What changes between the purchase and the sales book.
    _book_move_types = ('in_invoice',)
    # Signed amounts are negative on vendor bills, positive on customer invoices.
    _book_sign = -1
    _book_name = 'LIBRO DE COMPRAS'
    _book_partner_label = 'PROVEEDOR'
    _book_empty_error = (
        "Selecciona al menos una factura de proveedor "
        "(no se incluyen notas de crédito)."
    )

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        # From the folio dialog the records come in data (Odoo does not send docids then).
        moves = self.env['account.move'].browse(docids or data.get('res_ids') or []).exists()
        bills = moves.filtered(
            lambda m: m.move_type in self._book_move_types
            and (INCLUDE_FEE_SLIPS or not self._is_fee_slip(m))
        )
        if not bills:
            raise UserError(self._book_empty_error)

        company = bills.company_id
        if len(company) != 1:
            raise UserError("Todas las facturas seleccionadas deben ser de la misma compañía.")
        if company.account_fiscal_country_id.code != 'CL':
            raise UserError(f"El {self._book_name.capitalize()} solo está disponible para la compañía de Chile.")

        # The book's month comes from the accounting date.
        months = {(bill.date.year, bill.date.month) for bill in bills}
        if len(months) != 1:
            raise UserError(f"Selecciona facturas de un solo mes contable para imprimir el {self._book_name.capitalize()}.")
        year, month = months.pop()

        bills = bills.sorted(lambda m: (m.invoice_date or m.date, self._sort_key(self._document_number(m))))

        rows = []
        for number, bill in enumerate(bills, start=1):
            exempt, taxed, tax, total = self._get_amounts(bill)
            rows.append({
                'number': number,
                'date': (bill.invoice_date or bill.date).strftime('%d/%m/%Y'),
                'doc_code': self._document_code(bill),
                'doc_number': self._document_number(bill),
                'partner': bill.invoice_partner_display_name or bill.partner_id.name or '',
                'vat': bill.commercial_partner_id.vat or bill.partner_id.vat or '',
                'exempt': exempt,
                'taxed': taxed,
                'tax': tax,
                'total': total,
                'kind': self._kind(bill),
                'doc_type': bill.l10n_latam_document_type_id,
            })

        return {
            'doc_ids': bills.ids,
            'doc_model': 'account.move',
            'docs': bills,
            'company': company,
            'folio': data.get('folio'),
            'title': f"{self._book_name} {MONTHS[month - 1]} DE {year}",
            'partner_label': self._book_partner_label,
            'pages': self._split_pages(rows),
            'grand_totals': self._sum_rows(rows),
            'document_summary': self._document_summary(rows),
            'tax_summary': self._tax_summary(bills),
            'fmt_amount': self._format_amount,
        }

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    @api.model
    def _kind(self, bill):
        """ FACEE / FACEL / BHE from the start of the invoice number, else from the document type. """
        match = re.match(r'[A-Za-z]+', (bill.name or '').replace('-', ''))
        prefix = match.group(0).upper() if match else ''
        if prefix in KINDS:
            return prefix
        return DOCUMENT_TYPE_KINDS.get(bill.l10n_latam_document_type_id.code)

    @api.model
    def _is_fee_slip(self, bill):
        return self._kind(bill) == 'BHE' or bill.l10n_latam_document_type_id.code in FEE_SLIP_CODES

    @api.model
    def _get_amounts(self, bill):
        """ (M. EXENTO, M. AFECTO, I.V.A., TOTAL) in company currency.
        - Exempt (FACEE): the total goes to M. EXENTO and TOTAL.
        - FACEL / BHE: subtotal to M. AFECTO, taxes to I.V.A., subtotal + taxes to TOTAL.
        A document of unknown kind is treated as exempt only when it has no taxes.
        """
        untaxed = self._book_sign * bill.amount_untaxed_signed
        tax = self._book_sign * bill.amount_tax_signed
        total = self._book_sign * bill.amount_total_signed
        if self._is_exempt(bill, tax):
            return total, 0.0, 0.0, total
        return 0.0, untaxed, tax, untaxed + tax

    @api.model
    def _is_exempt(self, bill, tax):
        kind = self._kind(bill)
        return KINDS[kind]['exempt'] if kind else bill.company_id.currency_id.is_zero(tax)

    @api.model
    def _document_code(self, bill):
        kind = self._kind(bill)
        if kind:
            return KINDS[kind]['code']
        doc_type = bill.l10n_latam_document_type_id
        return doc_type.doc_code_prefix or doc_type.code or ''

    @api.model
    def _document_number(self, bill):
        """ Vendor bills: the supplier's folio (Referencia), only its number: "Fac 1312" -> "1312". """
        reference = (bill.ref or '').strip()
        match = re.fullmatch(r'\D*?(\d+)', reference)
        if match:
            return match.group(1)
        return reference or bill.l10n_latam_document_number or ''

    @api.model
    def _sort_key(self, number):
        """ Numeric folios sort as numbers (9 before 10), anything else after them as text. """
        return (0, int(number), '') if number.isdigit() else (1, 0, number)

    # ------------------------------------------------------------------
    # Pages, totals and summaries
    # ------------------------------------------------------------------

    @api.model
    def _sum_rows(self, rows):
        totals = {}
        for key in AMOUNT_KEYS:
            values = [row[key] for row in rows if row[key] is not None]
            totals[key] = sum(values) if values else None
        return totals

    @api.model
    def _add_totals(self, first, second):
        return {
            key: None if first[key] is None and second[key] is None else (first[key] or 0.0) + (second[key] or 0.0)
            for key in AMOUNT_KEYS
        }

    @api.model
    def _split_pages(self, rows):
        """ Fixed rows per page so that "TOTAL PAGINA" / "TOTAL ANTERIOR" always
        match what is printed on each sheet.
        """
        chunks = [rows[:ROWS_FIRST_PAGE]]
        rest = rows[ROWS_FIRST_PAGE:]
        while rest:
            chunks.append(rest[:ROWS_OTHER_PAGES])
            rest = rest[ROWS_OTHER_PAGES:]

        pages = []
        carried = dict.fromkeys(AMOUNT_KEYS)
        for index, chunk in enumerate(chunks):
            page_totals = self._sum_rows(chunk)
            pages.append({
                'rows': chunk,
                'previous_totals': carried if index else None,
                'page_totals': page_totals,
                'is_last': index == len(chunks) - 1,
            })
            carried = self._add_totals(carried, page_totals)
        return pages

    @api.model
    def _document_summary(self, rows):
        groups = {}
        for row in rows:
            groups.setdefault(row['doc_code'], []).append(row)

        summary = []
        for code, group_rows in groups.items():
            kind = group_rows[0]['kind']
            if kind:
                label = KINDS[kind]['label']
            else:
                label = (group_rows[0]['doc_type'].name or 'OTROS DOCUMENTOS').upper()
            summary.append({
                'count': len(group_rows),
                'label': label,
                'code': code,
                'totals': self._sum_rows(group_rows),
            })
        return sorted(summary, key=lambda s: s['code'], reverse=True)

    @api.model
    def _tax_summary(self, bills):
        """ Total per tax, from the tax journal items, in company currency. """
        amounts = defaultdict(float)
        for line in bills.line_ids.filtered('tax_line_id'):
            amounts[line.tax_line_id] += line.balance
        summary = []
        for tax, amount in amounts.items():
            summary.append({
                'group': (tax.tax_group_id.name or '').upper(),
                'name': (tax.name or '').upper(),
                'amount': amount,
            })
        return sorted(summary, key=lambda s: (s['group'], s['name']))

    @api.model
    def _format_amount(self, value):
        """ Chilean style, no decimals: 66188879 -> 66.188.879. Blank when pending (None). """
        if value is None:
            return ''
        return f"{round(value):,}".replace(',', '.')


class FeeBookReport(models.AbstractModel):
    """ Exactly the purchase book (same invoices and columns); only the title changes. """
    _name = 'report.pao_cl_purchase_sale_book_report.report_fee_book'
    _inherit = 'report.pao_cl_purchase_sale_book_report.report_purchase_book'
    _description = 'Reporte: Libro de honorarios (Chile)'

    _book_name = 'LIBRO DE HONORARIOS'


class SaleBookReport(models.AbstractModel):
    """ Same book for customer invoices and credit notes: title, partner column,
    folio and the exempt/taxed rule (by document type) change.
    """
    _name = 'report.pao_cl_purchase_sale_book_report.report_sale_book'
    _inherit = 'report.pao_cl_purchase_sale_book_report.report_purchase_book'
    _description = 'Reporte: Libro de ventas (Chile)'

    # Credit notes come out negative (signed amounts), so they subtract in the totals.
    _book_move_types = ('out_invoice', 'out_refund')
    _book_sign = 1
    _book_name = 'LIBRO DE VENTAS'
    _book_partner_label = 'CLIENTE'
    _book_empty_error = "Selecciona al menos una factura o nota de crédito de cliente."

    @api.model
    def _kind(self, bill):
        """ Sales: only from the document type (33 FAC-EL, 34 FAC-EE, 71 BHE). Any
        other type prints its own Odoo prefix (N/C, NCXE, BEL, ...) and name.
        """
        return DOCUMENT_TYPE_KINDS.get(bill.l10n_latam_document_type_id.code)

    @api.model
    def _is_exempt(self, bill, tax):
        code = bill.l10n_latam_document_type_id.code
        if code in SALE_EXEMPT_CODES:
            return True
        if code in SALE_TAXED_CODES:
            return False
        return bill.company_id.currency_id.is_zero(tax)

    @api.model
    def _document_number(self, bill):
        """ Customer invoices: our own folio. """
        return bill.l10n_latam_document_number or bill.name or ''
