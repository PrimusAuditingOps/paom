{
    'name': 'PAO: Totals company currency  in invoices',
    'version': '17.0.0.1.0',
    'author': 'Samuel Castro',
    'category': '',
    'website': 'https://www.paomx.com',
    'sequence': 1,
    'summary': """
        Delete Totals company currency  in invoices
    """,
    'description': """
        Delete Totals company currency  in invoices
    """,
    'depends': [
        'account',
    ],
    'data' : [
        'reports/account_move_report.xml',
    ],
    'assets': {
        'web.report_assets_common': [
        ],
        'web.assets_backend': [
        ],
    },
    'qweb': [],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
