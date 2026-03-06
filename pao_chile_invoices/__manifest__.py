{
    "name": "PAO: Chile Invoices Addon",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "https://paomx.com",
    "depends": ["base", "account"],
    'data': [
        'views/account_move_inherit_form.xml',
        'views/apply_exchange_rate_move_lines_wizard_view.xml',
        'views/product_product_inherit_form.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
}