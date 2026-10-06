# -*- coding: utf-8 -*-
{
    'name': 'PAO Sale Quote Chile',
    'version': '17.0.1.0.0',
    'author': 'samuel castro',
    'category': 'Sales',
    'website': 'https://paomx.com',
    'summary': """
        Editable regional quotation format (PDF and portal) for the Chilean company.
    """,
    'description': """
        Companies with a "Chile quotation format" print their quotations and orders with an editable HTML
        format: it is generated from the format of the quotation template (placeholders for the customer data
        and tables built from the order lines, with combined rows and amounts in the product base currency)
        and then freely edited by the salesperson. The PDF adds the logo header and the regional footer.
        Other companies keep the native Odoo format.
    """,
    'depends': ['sale_management', 'pao_chile_invoices'],
    'data': [
        # security
        'security/pao_quote_security.xml',
        'security/ir.model.access.csv',
        # data
        'data/report_paperformat_data.xml',
        # reports
        'report/pao_quote_report_templates.xml',
        'report/pao_quote_portal_templates.xml',
        # views
        'views/pao_quote_config_views.xml',
        'views/sale_order_views.xml',
        'views/pao_menu_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
}
