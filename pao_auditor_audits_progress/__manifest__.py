# -*- coding: utf-8 -*-
{
    'name': 'PAO Auditor Audits Progress',
    'version': '1.0',
    'author': 'Abrahan Barrios',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','purchase', 'servicereferralagreement','auditordaysoff','auditconfirmation','pao_assignment_auditor'
    ],
    'data': [
        # security
        'security/group.xml',
        'security/ir.model.access.csv',
        # data
        # reports
        # views
        'views/res_partner.xml'
    ],
}
