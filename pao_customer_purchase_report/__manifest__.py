{
    'name': 'PAO: Customer purchase report',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Purchase',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        This module adds the sales team relational fields and the
        invoice client, so that the information can be shown in more detail.
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'purchase',
        'crm'
    ],
    'data' : [
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
