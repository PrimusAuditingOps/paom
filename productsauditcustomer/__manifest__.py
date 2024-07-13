{
    'name': 'PAO: Products Audit Customer',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Sale',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Adds a new custom report called “Sales Analysis” to the sales application
        by Audited Product
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'sale',
        'servicereferralagreement',
        'comisionpromotores',
        'customergroups'
    ],
    'data' : [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/report_sale_audit_product_views.xml',
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
