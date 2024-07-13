# -*- coding: utf-8 -*-
{
    'name': 'PAO Operations Agenda',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to have an agenda to review the auditor's availability.
    """,
    'description': """
    v 1.0
        * Migrated from v14.\n
    """,
    'depends': ['base','sale','purchase','account','comisionpromotores','customergroups','auditordaysoff',
        'auditconfirmation','servicereferralagreement'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'views/purchase_order_operations_agenda.xml',
    ],
    'license': 'LGPL-3',
}
