{
    "name": "PAO SGC",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "https://paomx.com",
    "depends": ["approvals", "base"],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        
        'data/approval_category_data.xml',
        'data/departments_data.xml',
        'data/schemes_data.xml',
        
        'views/pao_approval_category_view.xml',
        'views/pao_documents_version_views.xml',
        'views/pao_wizards_view.xml',
        'views/pao_sgc_configuration.xml',
        'views/approval_request.xml',
        'views/menu_application_sgc.xml',
    ],
    'application': 'True'
}