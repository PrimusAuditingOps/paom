{
    'name': 'PAO: Employee signature',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Human Resource',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Add a digital signature to each employee form view
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'hr'
    ],
    'data' : [
        'views/hr_employee_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
        ],
        'web.assets_backend': [
        ],
    },
    'qweb': [],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
