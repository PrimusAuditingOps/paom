{
    'name': 'PAO: Attachment Download',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Accounting/Accounting',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Enable to download all the attachments related to each invoice
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'account',
        'pao_mxn_currency_group'
    ],
    'data' : [
        'data/attachment_data.xml',
        'views/ir_attachment_views.xml',
        'views/account_move_views.xml',
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
