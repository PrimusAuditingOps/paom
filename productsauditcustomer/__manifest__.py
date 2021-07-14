# -*- coding: utf-8 -*-
{
    'name': 'Products Audit Customer',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','sale','servicereferralagreement','comisionpromotores','customergroups'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'views/res_partner.xml',
        'views/report_sale_audit_product_views.xml',
    ],
}
