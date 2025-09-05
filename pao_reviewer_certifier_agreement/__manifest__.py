{
    "name": "PAO Reviewer Certifier Agreement",
    'version': '17.0.0.1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        The purpose of this module is to
    """,
    'description': """
        The purpose of this module is to
    """,
    'depends': ['base','purchase','servicereferralagreement','l10n_mx_edi_extended'
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        'data/certifier_agreement_data.xml',
        'data/reviewer_agreement_data.xml',
        # demo
        # reports
        'reports/agreement_header_footer_certifier.xml',
        'reports/agreement_header_footer_reviewer.xml',
        'reports/report_reviewer_certifier_agreements.xml',
        # views
        'views/product_template.xml',
        'views/purchase_order.xml',
        'views/reviewer_certifier_agreements.xml',
        'views/certifier_agreement.xml',
        'views/reviewer_agreement.xml',
        'views/reviewer_certifier_portal_template.xml',
    ],
     'assets': {
        'web.assets_frontend': [
            '/pao_reviewer_certifier_agreement/static/src/css/pao_reviewer_certifier_agreement.css',
        ],
    },
    'css': [
        'static/src/css/pao_reviewer_certifier_agreement.css',
    ],
    'license': 'LGPL-3',
}