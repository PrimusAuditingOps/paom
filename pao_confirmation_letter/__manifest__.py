# -*- coding: utf-8 -*-
{
    'name': 'PAO Confirmation Letter',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to send confirmation letter to the customers.
    """,
    'description': """
   
    """,
    'depends': ['base','sale','servicereferralagreement',
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        'reports/confirmation_letter_header_footer_gfs_english.xml',
        'reports/confirmation_letter_header_footer_gfs_spanish.xml',
        'reports/confirmation_letter_header_footer_gg_english.xml',
        'reports/confirmation_letter_header_footer_gg_spanish.xml',
        'reports/confirmation_letter_report_gfs_english.xml',
        'reports/confirmation_letter_report_gfs_spanish.xml',
        'reports/confirmation_letter_report_gg_english.xml',
        'reports/confirmation_letter_report_gg_spanish.xml',
        'reports/confirmation_letter_report.xml',
        # views
        'wizard/send_confirmation_letter.xml',
        'views/sale_order.xml',
        'views/confirmation_letter.xml',

    ],
    'license': 'LGPL-3',
}
