{
    'name': 'PAO: Account follow-up currency',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Accounting/Accounting',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Add the currency used in the transaction
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'account_followup'
    ],
    'data' : [
        'views/res_partner_views.xml',
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
