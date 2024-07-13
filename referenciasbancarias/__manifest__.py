{
    'name': 'PAO: Referencias bancarias',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Sale',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Payment reference in the contact, in turn add payment data in the PDF issued to the client
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'website',
        'account',
        'sale'
    ],
    'data' : [
        'data/ref_bank_sequence.xml',
        'views/res_partner_views.xml',
        'views/sale_order_portal_content.xml',
        'reports/sale_report.xml',
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
