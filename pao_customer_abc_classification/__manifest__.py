# -*- coding: utf-8 -*-
{
    'name': 'PAO Customer ABC Classification',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Clasifica Clientes, Grupos y Promotores en categorías ABC '
               'según su volumen de ventas de temporada',
    'description': """
Agrega un catálogo configurable de rangos de Categoría ABC (AAA/AA/A/B/C) y
un campo de Categoría ABC en Contactos (a nivel razón social), Grupos y
Promotores.

Un cron anual (rollover de temporada, septiembre-agosto) recalcula:
1. Por cada Grupo: suma las ventas USD de sus clientes y asigna la
   categoría resultante al grupo y a cada uno de sus clientes.
2. Por cada Promotor: igual, con sus clientes.
3. Clientes sin grupo ni promotor: categorización individual.

Las ventas se toman de sales.invoicing.report (USD, sin impuestos),
filtrando solo productos marcados como comisionables.
""",
    'author': 'Samuel Castro',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'sale',
        'sales_team',
        'customergroups',
        'comisionpromotores',
        'servicereferralagreement',
        'pao_sales_invoicing_report',
        'pao_customer_segmentation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/pao_abc_category_data.xml',
        'data/pao_abc_ir_cron_data.xml',
        'views/pao_abc_category_views.xml',
        'views/res_partner_views.xml',
        'views/customergroups_group_views.xml',
        'views/comisionpromotores_promotor_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
