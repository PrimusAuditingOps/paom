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
        'portal',
        'servicereferralagreement',
        'pao_assignment_auditor',
    ],
    'data' : [
        #'security/groups.xml',
        'data/multiple_proposal_template.xml',
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/portal_multiple_proposal.xml',

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