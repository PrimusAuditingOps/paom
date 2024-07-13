{
    'name': 'PAO: Customer Groups',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Partner',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        This module adds to odoo the functionality of managing groups of clients. For this,
        added a new model called “CustomerGroupsGroup" that contains the name of the
        group and the list of clients that comprise it
    """,
    'description': """
    v 1.0
        Reviewer : Dwiki Adnan F. <dwiki@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'sale',
        'account'
    ],
    'data': [
        'security/groups.xml',
        'security/ir_rules.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/account_move.xml',
        'views/customergroups_group.xml',
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
