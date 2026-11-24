{
    'name': 'PAO: Chile Report Folio',
    'version': '17.0.1.0.0',
    'author': 'Samuel Castro',
    'category': 'Accounting/Accounting',
    'website': 'https://paomx.com',
    'summary': """
        Shared dialog that asks for an optional folio before printing the
        Chilean PDF reports (Libro diario, compras, honorarios, ventas).
    """,
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/report_folio_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
