# -*- coding: utf-8 -*-
{
    'name': 'PAO Offices',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to have an office for customers.
    """,
    'description': """
    v 1.0
        * Migrated from v14.\n
    """,
    'depends': ['base','sale'
    ],
    'data': [
        # security
        'security/ir_rules.xml',
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'views/res_partner.xml',
        'views/pao_offices.xml',
    ],
    'license': 'LGPL-3',
}
