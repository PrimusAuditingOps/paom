{
    "name": "PAO: Sale Order Commissions",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "https://paomx.com",
    "depends": ["base", "sale", "servicereferralagreement"],
    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        
        'views/sale_commissions_report_views.xml',
        'views/sale_order_form_inherit.xml',
        'views/menus_sales_commissions.xml',
        
        'data/commissions_sources_data.xml'
    ],
    'license': 'LGPL-3',
}