{
    'name': 'PAO Suppliers Verificiation',
    'version': '1.0',
    'author': 'Manuel Uzueta Gil',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['contacts'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        'data/branches_data.xml',
        'data/services_data.xml',
        # reports
        # views
        'views/suppliers_configurations_views.xml',
        'views/res_partner_supplier_verifications_view.xml'
    ],
}
