# -*- coding: utf-8 -*-
{
    'name': 'PAO Sales Budget',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is 
    """,
    'description': """
    
    """,
    'category': 'Sales',
    'depends': ['base','product','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/vsq_budget_views.xml',
        'views/vsq_budget_flat_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
