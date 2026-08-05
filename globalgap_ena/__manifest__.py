# -*- coding: utf-8 -*-
{
    'name': 'GlobalGAP - Evaluaciones No Anunciadas (ENA)',
    'version': '17.0.1.0.0',
    'summary': 'Gestión del programa de auditorías no anunciadas GlobalGAP',
    'description': """
     
    """,
    'category': 'Quality',
    'author': 'Samuel Castro',
    'depends': ['base', 'mail', 'web','auditordaysoff','pao_globalgap_fans'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/sequence.xml',

        'wizard/lost_reason_wizard.xml',
        'views/ena_solicitud_views.xml',
        'views/ena_dashboard_views.xml',
        
        'wizard/ena_import_wizard_views.xml',
        

        
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'globalgap_ena/static/src/js/ena_dashboard.js',
            'globalgap_ena/static/src/views/ena_dashboard.xml',
            'globalgap_ena/static/src/css/ena_dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
