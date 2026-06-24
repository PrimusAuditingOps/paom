{
    "name": "PAO Expenses Portal",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "",
    "depends": ["hr_expense", "purchase_requisition"],
    'data': [
        'data/hr_expense_pivot_search_inherit.xml',
        
        'report/expenses_report_inherit.xml',
        
        'views/account_move_inherit.xml',
        'views/hr_employeee_form_inherit.xml',
        'views/expense_categories_view.xml',
        'views/expense_scheme_views.xml',
        'views/hr_expense_sheet_view.xml',
        'views/hr_expense_view.xml',
        'views/portal_expenses_view.xml',
        'views/portal_purchase_order_inherit.xml',
        'views/product_category_expense_inherit.xml',
        'views/purchase_order_form_inherit.xml',
        'views/upload_expense_statement.xml',
        
        'security/ir.model.access.csv',
        'security/rules.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pao_expenses_portal/static/src/js/portal.js',
        ],
    },
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}