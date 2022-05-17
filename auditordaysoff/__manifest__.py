# -*- coding: utf-8 -*-
{
    'name': 'auditor days off',
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
        #'security/groups.xml',
        
        # data
        # demo
        # reports
        # views
        'views/res_partner.xml',
        'views/purchase_order.xml',
        'views/auditor_days_off_days.xml',
        
    ],
}
