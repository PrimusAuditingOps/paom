# -*- coding: utf-8 -*-
{
    'name': 'PAO CR Visits Report',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to generate a report on clients and the audits they perform.
    """,
    'description': """
        The purpose of this module is to generate a report on clients and the audits they perform.
    """,
    'depends': ['base','sale','crm'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'views/cr_visits_report.xml',
        'views/cr_visits_report_services.xml',
    ],
    'license': 'LGPL-3',
}
