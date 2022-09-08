# -*- coding: utf-8 -*-
{
    'name': 'PAO Shippers',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','account','sale'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'views/res_partner.xml',
        'views/account_move.xml',
        'views/shippers.xml',
    ],
}
