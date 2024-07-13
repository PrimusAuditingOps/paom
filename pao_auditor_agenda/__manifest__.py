{
    'name': 'PAO: Auditor Agenda',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Portal',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        This module adds to the web portal a calendar with the days when an auditor will have purchase orders
        (will perform audits), as well as displaying the non-working days for them.
        This view is only available for auditor profiles.
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
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
            'pao_auditor_agenda/static/src/scss/website_auditor_calendar.scss'
        ],
    },
    'qweb': [],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}