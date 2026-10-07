# -*- coding: utf-8 -*-
{
    'name': 'PAO Sale Combo',
    'version': '17.0.1.0.0',
    'author': 'samuel castro',
    'category': 'Sales',
    'website': 'https://paomx.com',
    'summary': """
        Product combos priced per pricelist and added to quotations as a section.
    """,
    'description': """
        Catalog of product combos (e.g. GLOBALG.A.P. + Nurture). Each pricelist can include combos with a price
        per product. The "Add a combo" button of the quotation lines adds a section named after the combo with
        its products, priced with the combo prices of the quotation pricelist (0 when the combo or the product
        has no price in that pricelist). Only available for companies located in Chile.
    """,
    'depends': ['sale'],
    'data': [
        # security
        'security/pao_sale_combo_security.xml',
        'security/ir.model.access.csv',
        # views
        'views/pao_sale_combo_views.xml',
        'views/product_pricelist_views.xml',
        'wizard/pao_sale_combo_add_views.xml',
        'views/sale_order_views.xml',
        'views/pao_menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pao_sale_combo/static/src/views/**/*',
        ],
    },
    'license': 'LGPL-3',
}
