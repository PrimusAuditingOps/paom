# -*- coding: utf-8 -*-
{
    'name': 'Comision Promotores',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','account','sale','servicereferralagreement'
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
        'views/account_move_tree.xml',
        'views/comisionpromotores_promotor.xml',
        #'views/account_move_view_search.xml',
    ],
}
