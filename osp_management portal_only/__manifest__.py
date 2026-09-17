{
    'name': 'OSP Management Portal Only',
    'version': '17.0.1.0.0',
    'category': 'Operations/OSP',    
    'description': """
        
    """,
    'author': 'Hector Cortes',    
    'depends': ['base', 'mail', 'portal', 'website', 'web', 'osp_management'],
    'data': [
        'views/osp_users_views.xml',
        'views/osp_portal_templates.xml',
    ],    
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}