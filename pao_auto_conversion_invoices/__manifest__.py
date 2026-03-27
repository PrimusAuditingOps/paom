{
    "name": "PAO: Auto Conversion Invoices",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "https://paomx.com",
    "depends": ["base", "account", "pao_chile_invoices"],
    'data': [
        # 'views/account_move_inherit_form.xml',
        'views/auto_currency_conversion_wizard_view.xml',
        # 'views/product_product_inherit_form.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
}