# -*- coding: utf-8 -*-
{
    'name': 'audit confirmation',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','purchase','portal'
    ],
    'data': [
        # security
        #'security/groups.xml',
        'security/ir.model.access.csv',
        #'security/groups.xml',
        
        # data
        'data/mail_template_data.xml',
        # demo
        # reports
        # views
        'views/auditconfirmation.xml',
        'views/purchase_order.xml',
        'views/audit_state.xml',
    ],
}
