{
    'name': 'PAO: Chile Report Folio',
    'version': '17.0.1.1.0',
    'author': 'Samuel Castro',
    'category': 'Accounting/Accounting',
    'website': 'https://paomx.com',
    'summary': """
        Optional folio asked before printing the Chilean PDF reports (Libro
        diario, compras, honorarios, ventas, Balance General, Libro mayor).
        The folio goes up by one on every page (123, 124...).
    """,
    'depends': [
        'account_reports',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/folio_templates.xml',
        'views/report_folio_wizard_views.xml',
        'views/account_report_folio_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
