{
    'name': 'PAO: Auditor days off',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Purchase',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Show the days which Auditor is not available to carry out an audit
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'pao_catalog_menu'
    ],
    'data' : [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'views/res_partner.xml',
        'views/purchase_order.xml',
        'views/auditor_days_off_days.xml',
    ],
    'assets': {
        'web.report_assets_common': [
        ],
        'web.assets_backend': [
        ],
    },
    'qweb': [],
    'external_dependencies': {
        'python': ['tkinter', 'turtle']
    },
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
