# -*- coding: utf-8 -*-
{
    'name': 'PAO Sale Quote Chile',
    'version': '17.0.1.0.0',
    'author': 'samuel castro',
    'category': 'Sales',
    'website': 'https://paomx.com',
    'summary': """
        Regional quotation format (PDF and portal) for the Chilean company.
    """,
    'description': """
        Prints quotations of companies with a "Chile quotation format" configured
        using the regional layout: tables per order section, combined services
        (service + add-ons) printed as a single row, amounts shown in the product
        base currency, and additional information blocks selected by audit scheme.
        Confirmed orders and other companies keep the native Odoo format.
    """,
    'depends': ['sale_management', 'pao_chile_invoices'],
    'data': [
        # security
        'security/pao_quote_security.xml',
        'security/ir.model.access.csv',
        # data
        'data/report_paperformat_data.xml',
        'data/pao_quote_data.xml',
        # reports
        'report/pao_quote_report_templates.xml',
        'report/pao_quote_portal_templates.xml',
        # views
        'views/pao_quote_config_views.xml',
        'views/pao_quote_catalog_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/pao_menu_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
}
