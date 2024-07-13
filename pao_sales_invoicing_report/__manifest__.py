{
    "name": "PAO Sales Invoicing Report",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "https://paomx.com",
    "depends": ["account", "pao_shippers","pao_offices","pao_old_sales_team", "comisionpromotores"],
    'data': [
        'views/sales_invoicing_report_views.xml',
        'views/menu_item_accounting_sales_report.xml',
        
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
}