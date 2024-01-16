# -*- coding: utf-8 -*-
{
    'name': 'PAO Customer Registration',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base', 'website', 'l10n_mx_edi', 'currencyquotation',
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        #'data/cr_data.xml',
        # demo
        # reports
        # views
        'views/res_partner.xml',
        'views/customer_registration_request_view.xml',
        'views/customer_registration_view.xml',
    ],
    
}
