# -*- coding: utf-8 -*-
{
    'name': 'supplier taxes',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','purchase'
    ],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'views/supplier_taxes.xml',
        'views/res_partner.xml',
    ],
}
