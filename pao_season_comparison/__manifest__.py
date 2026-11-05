# -*- coding: utf-8 -*-
{
    'name': 'PAO Season Comparison',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'website': 'https://paomx.com',
    'summary': 'Comparativo de facturación y de coordinación, temporada vs temporada',
    'description': """
Comparativos de facturación y de coordinación entre dos temporadas
(1 sep - 31 ago), con reporte en pantalla y exportación a Excel.
    """,
    'category': 'Sales',
    'depends': [
        'sale',
        'pao_sales_budget',
        'pao_sales_invoicing_report',
        'servicereferralagreement',
        'purchase',
        'pao_customer_purchase_report',
        'pao_purchase_report_agenda',
        'auditconfirmation',
        'customergroups',
        'comisionpromotores',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pao_season_billing_views.xml',
        'views/pao_season_coordination_views.xml',
    ],
    'license': 'LGPL-3',
}
