# -*- coding: utf-8 -*-
{
    'name': 'PAO Mass Mailing Contact Tag',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """

    """,
    'description': """
   
    """,
    'depends': ['base','mass_mailing'
    ], 
    'data': [
        # security
        'security/ir.model.access.csv',
        'security/rules.xml',
        # data
        # demo
        # reports
        # views
        'views/mailing_contact.xml',
    ],
    'license': 'LGPL-3',
}
