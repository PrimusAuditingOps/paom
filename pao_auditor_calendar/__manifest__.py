{
    'name': 'PAO: Auditor Calendar',
    'version': '1.0',
    'author': 'Manuel Uzueta Gil',
    'category': 'Portal',
    'website': 'paomx.com',
    'sequence': 1,
    'depends': [
        'portal',
        'auditordaysoff',
        'auditconfirmation',
        'servicereferralagreement'
    ],
    'data' : [
        'views/auditor_agenda_portal.xml',
    ],
    'assets': {
        'web.report_assets_common': [
        ],
        'web.assets_backend': [
        ],
        'web.assets_frontend': [
        ],
    },
    'qweb': [],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}