{
    'name': 'PAO: Chile Journal Book Report',
    'version': '17.0.1.0.0',
    'author': 'Samuel Castro',
    'category': 'Accounting/Accounting',
    'website': 'https://paomx.com',
    'summary': """
        "Reporte: Libro diario" PDF for selected journal items (Chile only,
        one month at a time), with previous fiscal-year accumulations.
    """,
    'depends': [
        'account',
    ],
    'data': [
        'report/journal_book_report.xml',
        'report/journal_book_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
