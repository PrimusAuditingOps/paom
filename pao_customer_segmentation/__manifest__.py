# -*- coding: utf-8 -*-
{
    'name': 'PAO Customer Segmentation',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Classifies customers by structural segment (Key/Promoter/Individual) '
               'and by seasonal sales status (New/Recovered/Current)',
    'description': """
""",
    'author': 'Samuel Castro',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'account',
        'comisionpromotores',
        'customergroups',
        'servicereferralagreement',
    ],
    'data': [
        'security/pao_cs_security.xml',
        'data/pao_cs_ir_cron_data.xml',
        'views/pao_cs_res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
