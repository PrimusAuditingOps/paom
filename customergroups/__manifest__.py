# -*- coding: utf-8 -*-
{
    'name': 'Customer Groups',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','account','sale'
    ],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'views/res_partner.xml',
        'views/account_move.xml',
        'views/customergroups_group.xml',
    ],
}
