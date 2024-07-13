{
    'name': 'PAO: Shippers',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Purchase',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        The objective of this module is to add to odoo the functionality of managing distributors of
        customers. contains the distributor name and list of affiliated customers
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'base',
        'account',
        'sale'
    ],
    'data' : [
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/pao_shippers_views.xml',
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
