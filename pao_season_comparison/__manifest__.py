# -*- coding: utf-8 -*-
{
    'name': 'PAO Season Comparison',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'website': 'https://paomx.com',
    'summary': 'Comparativo de facturación (y coordinación) temporada vs temporada',
    'description': """
Comparativo de facturación por cliente y esquema entre dos temporadas
(1 sep - 31 ago), con dos interfaces: reporte en pantalla y lista dinámica
(filtros, favoritos, pivot), más exportación a Excel.
    """,
    'category': 'Sales',
    'depends': [
        'sale',
        'pao_sales_budget',
        'pao_sales_invoicing_report',
        'servicereferralagreement',
        'customergroups',
        'comisionpromotores',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pao_season_billing_views.xml',
    ],
    'license': 'LGPL-3',
}
