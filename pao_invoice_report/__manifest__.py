{
    "name": "PAO Invoice Report",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "https://paomx.com",
    "depends": ["account", "pao_assignment_auditor", "attachmentdownload"],
    'data': [
        'views/invoice_report_views.xml',
        'views/menu_item_invoice_report.xml',
        
        'security/ir.model.access.csv',
        'security/rules.xml',
    ],
    'license': 'LGPL-3',
}