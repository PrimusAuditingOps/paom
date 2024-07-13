{
    'name': 'PAO: Edit Sale Order Date',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'N/A',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Access to the date_order field has been modified, you can now change the
        date on which a sales order was created or confirmed, as long as the user has
        with the permissions to do so.
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'sale'
    ],
    'data' : [
        'security/groups.xml',
        'views/sale_order_views.xml',
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
