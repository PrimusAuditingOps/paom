{
    'name': 'PAO: Currency Quotation',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Sale',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        The purpose of this module is to add to the print document and web
        the sales order, a description of the type of currency in which the
        quantities of it.
    """,
    'description': """
    v 1.0
        Reviewer : Dwiki Adnan F. <dwiki@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'sale'
    ],
    'data': [
        'reports/sale_report.xml',
        # 'views/res_partner_views.xml',
        'views/sale_order_portal_views.xml',
    ],
    'assets': {

    },
    'qweb': [
        
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
