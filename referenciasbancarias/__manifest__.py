# -*- coding: utf-8 -*-
{
    'name': 'referencias bancarias',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','website','account','sale'
    ],
    'data': [
        # security
        # data
        'data/ref_bank_sequence.xml',
        # demo
        # reports
        # views
        'views/res_partner.xml',
        'views/sale_order_portal_content.xml',
        'reports/sale_report_inherit.xml',
        'reports/account_move_report_inherit.xml',
    ],
}
