{
    'name': 'PAO: Sign RA',
    'version': '17.0.0.1.0',
    'author': 'Manuel Uzueta',
    'website': 'https://www.paomx.com',
    'depends': [
        'auditconfirmation', 'servicereferralagreement'
    ],
    'data' : [
        # 'security/groups.xml',
        'security/ir.model.access.csv',
        'data/ra_availability_mail_template.xml',
        'data/ra_mail_templates_default.xml',
        # 'security/ir_rules.xml',
        # 'views/res_partner.xml',
        'views/ra_report_foreign_company.xml',
        'views/purchase_order.xml',
        'views/ra_mail_templates_views.xml',
        'views/sign_ra_template_portal.xml',
        'views/ra_document_views.xml',
        'views/send_ra_view_form.xml',
    ],

    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
