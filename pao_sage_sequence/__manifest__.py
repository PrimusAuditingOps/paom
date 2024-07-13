{
    'name': 'PAO: Sage Sequence',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Accounting',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        It is intended to add a new field called pao_sage_folio
    """,
    'description': """
    v 1.0
        Reviewer : Dwiki Adnan F. <dwiki@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'account'
    ],
    'data' : [
        'data/ref_sage_sequence.xml',
        'views/account_move_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
        ],
        'web.assets_frontend': [
        ],
    },
    'qweb': [],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
