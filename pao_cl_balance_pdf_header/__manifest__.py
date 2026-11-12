{
    'name': 'PAO: Chile Balance PDF Header',
    'version': '17.0.1.0.0',
    'author': 'Samuel Castro',
    'category': 'Accounting/Accounting',
    'website': 'https://paomx.com',
    'summary': """
        Custom title and company header in the PDF of the Chilean
        8-column fiscal balance report (Balance General), with an optional
        folio asked before printing.
    """,
    'depends': [
        'l10n_cl_reports',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pdf_export_templates.xml',
        'views/folio_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
