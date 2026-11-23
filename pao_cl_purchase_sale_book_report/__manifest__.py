{
    'name': 'PAO: Chile Purchase and Sales Book Reports',
    'version': '17.0.1.0.0',
    'author': 'Samuel Castro',
    'category': 'Accounting/Accounting',
    'website': 'https://paomx.com',
    'summary': """
        "Reporte: Libro de compras", "Reporte: Libro de honorarios" (same
        content, other title) and "Reporte: Libro de ventas" PDFs for selected vendor bills / customer
        invoices (Chile only, one month at a time), with page totals and
        summaries by document type and tax.
    """,
    'depends': [
        'l10n_cl',
    ],
    'data': [
        'report/book_report.xml',
        'report/book_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
