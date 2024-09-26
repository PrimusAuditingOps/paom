# -*- coding: utf-8 -*-
{
    'name': 'PAO SIGN SA',
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to send clients' SA to signature.
    """,
    'description': """
    v 1.0
        * Migrated from v14.\n
    """,
    'depends': ['base','sale','servicereferralagreement','portal','pao_org_rn_audit_information'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        'security/rules.xml',
        # data
        'data/sa_data.xml',
        'data/cron_data.xml',
        'data/mail_template_data.xml',
        # demo
        # reports
        'reports/report_service_agreements.xml',
        'reports/sa_header_footer_ggap.xml',
        'reports/sa_header_footer_gfs.xml',
        'reports/sa_header_footer_nop.xml',
        'reports/sa_header_footer_smeta.xml',
        'reports/sa_header_footer_standard.xml',
        'reports/sa_header_footer_nop_lpo.xml',
        'reports/sa_header_footer_haccp.xml',
        'reports/sa_header_footer_lpo_ue.xml',
        'reports/sa_header_footer_sustentabilidad.xml',
        'reports/sa_header_footer_add_ggap.xml',
        'reports/sa_header_footer_gfs_usa.xml',
        
        # views
        'views/sa_portal_template.xml',
        'views/sa_pgfs_scheme.xml',
        'views/sa_globalgap_scheme.xml',
        'views/sa_nop_lpo_scheme.xml',
        'views/sa_smeta_scheme.xml',
        'views/sa_nop_scheme.xml',
        'views/sa_primus_standar_scheme.xml',
        'views/sa_lpo_ue_scheme.xml',
        'views/sa_haccp_scheme.xml',
        'views/sa_send_request_view.xml',
        'views/sale_order.xml',
        'views/sa_agreements_sent.xml',
        'views/sa_sustentabilidad_scheme.xml',
        'views/sa_add_globalgap_scheme.xml',
        'views/sa_pgfs_scheme_usa.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/pao_sign_sa/static/src/css/pao_sign_sa.css',
        ],
    },
    'css': [
        'static/src/css/sa.css',
    ],
    'license': 'LGPL-3',
}
