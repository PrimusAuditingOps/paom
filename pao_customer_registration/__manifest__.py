# -*- coding: utf-8 -*-
{
    'name': 'PAO Customer Registration',
    'version': '17.0.0.1.0',
    'author': 'Samuel Castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to allow customers to update their tax information.
    """,
    'description': """
    v 1.0
        * Migrated from v14.\n
    """,

    'depends': ['base','web', 'website', 'l10n_mx_edi', 'currencyquotation',
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        #'data/cr_data.xml',
        # demo
        # reports
        # views
        'views/res_partner.xml',
        'views/customer_registration_request_view.xml',
        'views/customer_registration_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'https://unpkg.com/gridjs/dist/gridjs.umd.js',
            'https://unpkg.com/gridjs/dist/theme/mermaid.min.css',
            '/pao_customer_registration/static/src/js/pao_customer_registration.js',
        ],
    },
    'license': 'LGPL-3',
    
}
