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
    'depends': ['base','account','servicereferralagreement','pao_sign_ra'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'wizard/platform_audit_wizard.xml',
        'views/azz_platform_audits.xml',
        'views/azz_audit_template.xml',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'license': 'LGPL-3',
}
