{
    'name': 'PAO: Chile Balance PDF Header',
    'version': '17.0.1.1.0',
    'author': 'Samuel Castro',
    'category': 'Accounting/Accounting',
    'website': 'https://paomx.com',
    'summary': """
        Custom title and company header in the PDF of the Chilean
        8-column fiscal balance report (Balance General). The optional folio
        (one per page) comes from pao_cl_report_folio.
    """,
    'depends': [
        'l10n_cl_reports',
        'pao_cl_report_folio',
    ],
    'data': [
        'views/pdf_export_templates.xml',
        'views/report_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
