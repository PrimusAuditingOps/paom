{
    'name': 'PAO Administración de OSP',
    'version': '17.0.1.0.0',
    'category': 'Operations/OSP',
    'summary': 'Gestión de formularios OSP para Crop y Handler',
    'description': """
        Módulo para la administración de solicitudes OSP.
        Permite a los clientes externos llenar formularios desde el portal y a los administradores gestionarlos.
    """,
    'author': 'Hector Cortes',
    'depends': ['base', 'mail', 'portal'],
    'data': [
        'security/osp_security.xml',
        'security/ir.model.access.csv',
        'views/osp_menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}