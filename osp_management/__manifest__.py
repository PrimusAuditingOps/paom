{
    'name': 'OSP Management',
    'version': '17.0.1.6.0',
    'category': 'Operations/OSP',
    'summary': 'OSP form management for Crop and Handler',
    'description': """
        Module for managing OSP requests.
        Lets external customers fill out forms from the portal, and administrators manage them.
    """,
    'author': 'Hector Cortes',
    # 'website': el formulario público (sin login) usa website.layout como
    # cascarón visual — ver views/osp_form_crop.xml (public_osp_form_crop)
    # y views/osp_public_templates.xml.
    # 'web': el reporte PDF (report/osp_report_templates.xml) usa
    # web.html_container directamente.
    'depends': ['base', 'mail', 'portal', 'website', 'web'],
    'data': [
        'security/osp_security.xml',
        'security/ir.model.access.csv',
        'data/osp_service_data.xml',
        'data/osp_form_template_data.xml',
        # report/ ANTES que osp_menu_views.xml: la ficha admin tiene un
        # botón `type="action"` que referencia `%(osp_management.action_report_osp)d`
        # — ese xmlid debe existir ya al parsear ese botón.
        'report/osp_report_templates.xml',
        'views/osp_menu_views.xml',
        'views/osp_portal_templates.xml',
        'views/osp_form_crop.xml',
        'views/osp_form_handler.xml',
        'views/osp_form_handler_trader.xml',
        'views/osp_form_manejo_proceso.xml',
        'views/osp_form_comercializador.xml',
        'views/osp_form_cultivo.xml',
        'views/osp_public_templates.xml',
    ],
    # --- ASÍ SE REGISTRA EL JAVASCRIPT EN ODOO 17 ---
    'assets': {
        'web.assets_frontend': [
            'osp_management/static/src/js/osp_form.js',
        ],
        'web.assets_backend': [
            'osp_management/static/src/xml/osp_admin_form_view.xml',
            'osp_management/static/src/js/osp_admin_form_view.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}