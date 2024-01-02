# -*- coding: utf-8 -*-
{
    'name': 'PAO CR Gain Loss Tracker',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','crm','servicereferralagreement','comisionpromotores','customergroups'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        'data/mail_template_data.xml',
        # demo
        # reports        
        # views
        'views/res_partner.xml',
        'views/crm_schemes_view.xml',
        'views/crm_lead_view.xml',
        'views/crm_cr_cb_view.xml',
        'views/crm_view.xml',
    ],
}
