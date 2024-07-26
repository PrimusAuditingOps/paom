{
    'name': 'PAO: Multiple Proposal Auditor',
    'version': '17.0.0.1.0',
    'author': 'Samuel Castro',
    'category': 'Human Resource',
    'website': 'https://www.paomx.com',
    'sequence': 1,
    'summary': """
        Its objective is to send audit proposals to several auditors.
    """,
    'description': """
    v 1.0
    """,
    'depends': [
        'base',
        'pao_base',
        'purchase',
        'web',
        'servicereferralagreement',
    ],
    'data' : [
        #'security/groups.xml',
        #'security/ir.model.access.csv',
        #'views/res_partner_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            #'/pao_assignment_auditor/static/src/xml/**/*',
            #'/pao_assignment_auditor/static/src/js/**/*',
        ],
    },
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}