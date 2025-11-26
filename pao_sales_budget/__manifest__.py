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
    'category': '',
    'depends': ['base','product','sale','comisionpromotores','customergroups','crm'],
    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/pao_sales_budget.xml',
        'views/crm_team.xml',
        'views/customergroups_group.xml',
        'views/comisionpromotores.xml',
        'views/pao_sales_budget_line.xml',
        'views/product_template.xml',
        'views/pao_sales_budget_scheme.xml',
        
    ],
    'license': 'LGPL-3',
}
