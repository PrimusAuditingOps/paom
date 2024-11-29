# -*- coding: utf-8 -*-
{
    'name': "PRM ACCOUNT",

    'summary': """""",

    'description': """

    """,

    'author': "otorresmx (otorres@proogeeks.com)",
    'website': "http://proogeeks.com",

    # Categories can be used to filter modules in modules listing
    'category': 'Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_accountant', 'prm_contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
    ]
}

