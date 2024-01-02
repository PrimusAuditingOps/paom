# -*- coding: utf-8 -*-
{
    'name': 'PAO MASTER SALES ORDER',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','sale', 'servicereferralagreement','product','pao_sign_sa',
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        # demo
        # reports        
        # views
        'views/pao_child_sales_order_line_view.xml',
        'views/res_partner.xml',
        'views/product_pricelist.xml',
    ],
}
