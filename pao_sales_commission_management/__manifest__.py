# -*- coding: utf-8 -*-
{
    'name': 'PAO Sales Commission Management',
    'version': '17.0.1.0.0',
    'category': 'Sales/Commissions',
    'summary': 'Administration and control of sales commission payments '
               '(salespeople, external promoters, and coordinators)',
    'description': """
""",
    'author': 'Samuel Castro',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'sale_management',
        'purchase',
        'account',
        'comisionpromotores',
        'pao_quotation_consultant',
        'servicereferralagreement',
        'pao_customer_segmentation',
    ],
    'data': [
        'security/pao_sales_commission_security.xml',
        'security/ir.model.access.csv',
        'data/pao_ir_sequence_data.xml',
        'data/pao_ir_cron_data.xml',
        'views/pao_comisionpromotores_promotor_inherit_views.xml',
        'views/pao_sale_order_views.xml',
        'views/pao_sales_commission_views.xml',
        'views/pao_menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
