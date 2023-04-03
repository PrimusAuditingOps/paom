# -*- coding: utf-8 -*-
{
    'name': 'PAO Operations Agenda',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','sale','purchase','account','comisionpromotores','customergroups','auditordaysoff',
        'auditconfirmation','servicereferralagreement'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'views/purchase_order_operations_agenda.xml',
    ],
}
