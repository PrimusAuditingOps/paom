{
    'name': 'PAO: Service referral agreement',
    'version': '17.0.0.2.0',
    'author': 'Port Cities',
    'category': 'N/A',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Service referral agreement
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'pao_base',
        'sale',
        'account',
        'employeesignature',
        'auditordaysoff',
        'pao_catalog_menu'
    ],
    'data' : [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'reports/sustentabilidad.xml',
        'reports/haccp.xml',
        'reports/nop_lpo.xml',
        'reports/standard.xml',
        'reports/nop.xml',
        'reports/smeta.xml',
        'reports/ggap.xml',
        'reports/gfs.xml',
        'reports/header_footer_sustentabilidad.xml',
        'reports/header_footer_gfs.xml',
        'reports/header_footer_ggap.xml',
        'reports/header_footer_add_ggap.xml',
        'reports/header_footer_nop.xml',
        'reports/header_footer_haccp.xml',
        'reports/header_footer_smeta.xml',
        'reports/header_footer_lpo.xml',
        'reports/header_footer_lpo_ue.xml',
        'reports/header_footer_nop_lpo.xml',
        'reports/header_footer_standard.xml',
        'reports/header_footer_ra_general.xml',
        'reports/header_footer_ra_gfs.xml',

        'reports/header_footer_sustainability_usa.xml',
        'reports/header_footer_standard_usa.xml',
        'reports/header_footer_smeta_usa.xml',
        'reports/header_footer_gfs_usa.xml',
        'reports/header_footer_fsma_usa.xml',
        'reports/smeta_usa.xml',
        'reports/gfs_usa.xml',
        'reports/fsma_usa.xml',
        'reports/standard_usa.xml',
        'reports/sustentabilidad_usa.xml',

        'reports/sasaleorder.xml',
        'reports/rapurchaseorder.xml',
        'reports/lpo_ue.xml',
        'reports/add_ggap.xml',
        'reports/account_move_report.xml',
        'reports/sale_report.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/res_partner.xml',
        'views/organization.xml',
        'views/registrynumber.xml',
        'views/scheme.xml',
        'views/auditproducts.xml',
        'views/product_template.xml',
        'views/purchase_order_agenda.xml',
        'views/auditor_exchange_rate.xml',
        'views/percentage_of_audit_fee.xml',
        'views/audit_type.xml'
    ],
    'assets': {
        'web.report_assets_common': [
        ],
        'web.assets_backend': [
        ],
    },
    'css': [
        'static/src/css/servicereferralagreement.css',
    ],
    'qweb': [],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
