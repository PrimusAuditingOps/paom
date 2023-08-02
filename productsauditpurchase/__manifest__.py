# -*- coding: utf-8 -*-
{
    'name': 'Products Audit Purchase',
    'version': '1.0',
    'author': 'Abrahan Barrios',
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
        'views/report_purchase_audit_product_views.xml',
    ],
}
