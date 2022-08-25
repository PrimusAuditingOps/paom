# -*- coding: utf-8 -*-
{
    'name': 'service referral agreement',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','sale','purchase','account','employeesignature','auditordaysoff'
    ],
    'data': [
        # security
        #'security/groups.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        'reports/servicereferralagreement_header_footer_gfs.xml',
        'reports/servicereferralagreement_header_footer_ggap.xml',
        'reports/servicereferralagreement_header_footer_nop.xml',
        'reports/servicereferralagreement_header_footer_smeta.xml',
        'reports/servicereferralagreement_header_footer_lpo.xml',
        'reports/servicereferralagreement_header_footer_lpo_ue.xml',
        'reports/servicereferralagreement_header_footer_nop_lpo.xml',
        'reports/servicereferralagreement_header_footer_standard.xml',
        'reports/servicereferralagreement_header_footer_ra_general.xml',
        'reports/servicereferralagreement_header_footer_ra_gfs.xml',
        'reports/servicereferralagreement_sasaleorder.xml',
        'reports/servicereferralagreement_rapurchaseorder.xml',
        'reports/servicereferralagreement_lpo_ue.xml',
        'reports/account_move_report.xml',
        'reports/sale_report.xml',
        # views
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/res_partner.xml',
        'views/servicereferralagreement_organization.xml',
        'views/servicereferralagreement_registrynumber.xml',
        'views/servicereferralagreement_scheme.xml',
        'views/servicereferralagreement_auditproducts.xml',
        'views/product_template.xml',
        'views/purchase_order_agenda.xml',
        'views/servicereferralagreement_auditor_exchange_rate.xml',
        'views/servicereferralagreement_percentage_of_audit_fee.xml',
        'views/servicereferralagreement_audit_type.xml'
    ],
    'css': [
        'static/src/css/servicereferralagreement.css',
    ],
}
