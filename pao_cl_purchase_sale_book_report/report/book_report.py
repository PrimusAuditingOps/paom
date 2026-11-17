from collections import defaultdict

from odoo import api, models
from odoo.exceptions import UserError

MONTHS = [
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO',
    'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
]

# Chilean (SII) document type code -> (code shown in DOCUMENTO, label used in RESUMEN)
DOCUMENT_TYPES = {
    '33': ('FAC-EL', 'FACTURAS ELECT.'),
    '34': ('FAC-EE', 'FACTURAS ELECT. EXENTAS'),
}
# Boletas de honorarios (electronic and paper) are left out of this book.
FEE_SLIP_CODES = {'70', '71'}

# Rows that fit on a page: the first page has no "TOTAL ANTERIOR" row.
ROWS_FIRST_PAGE = 34
ROWS_OTHER_PAGES = 33

AMOUNT_KEYS = ('exempt', 'taxed', 'tax', 'total')


class PurchaseBookReport(models.AbstractModel):
    _name = 'report.pao_cl_purchase_sale_book_report.report_purchase_book'
    _description = 'Reporte: Libro de compras (Chile)'

    # What changes between the purchase and the sales book.
    _book_move_type = 'in_invoice'
    _book_name = 'LIBRO DE COMPRAS'
    _book_partner_label = 'PROVEEDOR'
    _book_empty_error = (
        "Selecciona al menos una factura de proveedor "
        "(no se incluyen notas de crédito ni boletas de honorarios)."
    )

    @api.model
    def _get_report_values(self, docids, data=None):
        moves = self.env['account.move'].browse(docids).exists()
        bills = moves.filtered(
            lambda m: m.move_type == self._book_move_type
            and m.l10n_latam_document_type_id.code not in FEE_SLIP_CODES
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
            exempt, taxed = self._get_exempt_and_taxed(bill)
            rows.append({
                'number': number,
                'date': (bill.invoice_date or bill.date).strftime('%d/%m/%Y'),
                'doc_code': self._document_code(bill),
                'doc_number': self._document_number(bill),
                'partner': bill.invoice_partner_display_name or bill.partner_id.name or '',
                'vat': bill.commercial_partner_id.vat or bill.partner_id.vat or '',
                'exempt': exempt,
                'taxed': taxed,
                'tax': abs(bill.amount_tax_signed),
                'total': abs(bill.amount_total_signed),
                'doc_type': bill.l10n_latam_document_type_id,
            })

        return {
            'doc_ids': bills.ids,
            'doc_model': 'account.move',
            'docs': bills,
            'company': company,
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
    def _get_exempt_and_taxed(self, bill):
        """ M. EXENTO / M. AFECTO: pending definition, printed blank for now.
        Return the two amounts here once the rule is decided.
        """
        return None, None

    @api.model
    def _document_code(self, bill):
        doc_type = bill.l10n_latam_document_type_id
        if doc_type.code in DOCUMENT_TYPES:
            return DOCUMENT_TYPES[doc_type.code][0]
        return doc_type.doc_code_prefix or doc_type.code or ''

    @api.model
    def _document_number(self, bill):
        """ Vendor bills: the supplier's folio (Referencia). """
        return bill.ref or bill.l10n_latam_document_number or ''

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
            doc_type = row['doc_type']
            group = groups.setdefault(doc_type.id, {'doc_type': doc_type, 'rows': []})
            group['rows'].append(row)

        summary = []
        for group in groups.values():
            doc_type = group['doc_type']
            label = DOCUMENT_TYPES.get(doc_type.code, (None, (doc_type.name or 'SIN TIPO DE DOCUMENTO').upper()))[1]
            summary.append({
                'count': len(group['rows']),
                'label': label,
                'code': group['rows'][0]['doc_code'],
                'totals': self._sum_rows(group['rows']),
            })
        return sorted(summary, key=lambda s: s['code'])

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


class SaleBookReport(models.AbstractModel):
    """ Same book for customer invoices: only the title, the partner column and
    the folio change.
    """
    _name = 'report.pao_cl_purchase_sale_book_report.report_sale_book'
    _inherit = 'report.pao_cl_purchase_sale_book_report.report_purchase_book'
    _description = 'Reporte: Libro de ventas (Chile)'

    _book_move_type = 'out_invoice'
    _book_name = 'LIBRO DE VENTAS'
    _book_partner_label = 'CLIENTE'
    _book_empty_error = "Selecciona al menos una factura de cliente (no se incluyen notas de crédito)."

    @api.model
    def _document_number(self, bill):
        """ Customer invoices: our own folio. """
        return bill.l10n_latam_document_number or bill.name or ''
