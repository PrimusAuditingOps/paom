# -*- coding: utf-8 -*-
{
    'name': 'PAO Platform Audits',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to .
    """,
    'description': """
    
    """,
    'depends': ['base','sale','account','servicereferralagreement','pao_sign_ra','pao_master_sales_order'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        'security/security.xml',
        # data
        # demo
        # reports
        # views
        'wizard/platform_audit_wizard.xml',
        'views/azz_platform_audits.xml',
        'views/azz_audit_template.xml',
        'views/azz_audit_coordinator.xml',
        'views/sales_report_views.xml',
        'view/product_template.xml',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'license': 'LGPL-3',
}
