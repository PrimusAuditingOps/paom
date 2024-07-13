# -*- coding: utf-8 -*-
{
    'name': 'PAO Products Audit Purchase',
    'version': '17.0.0.1.0',
    'author': 'Samuel Castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to have a purchase report per audited product.
    """,
    'description': """
    v 1.0
        * Migrated from v14.\n
    """,

    'depends': ['base','sale','purchase','servicereferralagreement','comisionpromotores','customergroups','auditconfirmation'
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
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
