# -*- coding: utf-8 -*-
{
    'name': 'PAO ORG and RN Audit Information',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to select an organization and registration number once per quote.
    """,
    'description': """
        The purpose of this module is to select an organization and registration number once per quote.
    """,
    'depends': ['base','servicereferralagreement'
    ],
    'data': [
        # security
        # data
        # demo
        # reports
        # views
        'views/sale_order.xml',
    ],
    'license': 'LGPL-3',
}
