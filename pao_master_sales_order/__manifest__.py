# -*- coding: utf-8 -*-
{
   'name': 'PAO MASTER SALES ORDER',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to create child orders from a quote.
    """,
    'description': """
        The purpose of this module is to create child orders from a quote.
    """,
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
        #'views/product_pricelist.xml',
        'views/purchase_order.xml',
    ],
    'license': 'LGPL-3',
}
