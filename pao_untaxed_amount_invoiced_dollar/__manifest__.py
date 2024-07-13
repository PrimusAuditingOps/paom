{
    'name': 'PAO: Untaxed Amount Invoiced Dollar',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Sale',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Add a new measure to the sales report graph, that represents
        the amount of audits sold in dollars without invoiced taxes.
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
