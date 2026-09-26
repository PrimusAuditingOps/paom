{
    'name': 'IT Asset Management',
    'version': '17.0.1.0.0',
    'category': 'Operations/IT',
    'summary': 'IT asset and software license management (ITAM & SAM)',
    'description': """
        Register, assign and control the organization's IT assets (hardware),
        software subscriptions and licenses across their whole lifecycle,
        from acquisition to retirement or renewal.
    """,
    'author': 'Hector Cortes',
    # 'hr': los activos se asignan a empleados/departamentos.
    # 'purchase': referencia opcional a la PO (y su línea) de compra.
    # 'account': referencia opcional a la factura/póliza.
    # 'analytic': distribución analítica del activo (analytic.mixin).
    'depends': ['base', 'mail', 'hr', 'purchase', 'account', 'analytic'],
    'data': [
        'security/pao_it_asset_security.xml',
        'security/ir.model.access.csv',
        'data/pao_it_asset_data.xml',
        'data/pao_it_asset_data_update.xml',
        'views/pao_it_catalog_views.xml',
        'views/pao_it_asset_movement_views.xml',
        'views/pao_it_asset_views.xml',
        # Menús al final: referencian las acciones definidas arriba.
        'views/pao_it_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
