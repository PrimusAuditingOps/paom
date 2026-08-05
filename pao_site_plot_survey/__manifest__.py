# -*- coding: utf-8 -*-
{
    'name': 'PAO Site Plot Survey',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Draw or import site/plot polygons on satellite view for quotations, '
               'and route them to Calidad for service estimate review',
    'description': """
""",
    'author': 'Samuel Castro',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'sale_management',
    ],
    'data': [
        'security/pao_site_plot_survey_security.xml',
        'security/ir.model.access.csv',
        'wizard/pao_site_plot_import_wizard_views.xml',
        'views/pao_site_plot_views.xml',
        'views/pao_site_plot_overview_map_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pao_site_plot_survey/static/src/js/**/*',
            'pao_site_plot_survey/static/src/xml/**/*',
            'pao_site_plot_survey/static/src/scss/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
