# -*- coding: utf-8 -*-
{
    'name': 'PAO GlobalGAP - Evaluaciones No Anunciadas (ENA)',
    'version': '17.0.1.0.0',
    'summary': 'Gestión del programa de auditorías no anunciadas GlobalGAP',
    'description': """

    """,
    'category': 'Quality',
    'author': 'Samuel Castro',
    'depends': ['base', 'mail', 'web','auditordaysoff','pao_globalgap_fans','auditconfirmation'],
    'data': [
        'security/pao_ena_security.xml',
        'security/ir.model.access.csv',
        'data/pao_mail_template_data.xml',
        'data/pao_ir_sequence_data.xml',

        'wizard/pao_lost_reason_wizard_views.xml',
        'views/pao_ena_solicitud_views.xml',
        'views/pao_ena_dashboard_views.xml',

        'wizard/pao_ena_import_wizard_views.xml',



        'views/pao_menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pao_globalgap_ena/static/src/js/pao_ena_dashboard.js',
            'pao_globalgap_ena/static/src/views/pao_ena_dashboard.xml',
            'pao_globalgap_ena/static/src/css/pao_ena_dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
