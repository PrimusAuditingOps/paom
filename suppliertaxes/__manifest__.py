{
    'name': 'PAO: Supplier taxes',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'N/A',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Allows you to manage the tax types of the auditors that will be considered when
        time to place purchase orders.
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'purchase',
        'pao_catalog_menu'
    ],
    'data' : [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'views/supplier_taxes_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
        ],
        'web.assets_backend': [
        ],
    },
    'css': [
    ],
    'qweb': [],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
