{
    'name': 'PAO: Promoter Portal Manager',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Website',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Its functionality is to create a section on the company's website,
        called External Implementers, which is linked to a submenu in the sales module for editing
        the CV of each auditor, which appears on the website if changes are made.
    """,
    'description': """
    v 1.0
        Reviewer : Dwiki Adnan F. <dwiki@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'portal', 'sales_team', 'website'
    ],
    'data' : [
        'security/ir_rules.xml',
        'security/ir.model.access.csv',
        'views/promoter_cv.xml',
        'views/promoter_portal_manager.xml',
    ],
    'assets': {
        'web.report_assets_common': [
        ],
        'web.assets_frontend': [
            'pao_promoter_portal_manager/static/src/scss/promoter_portal_manager.scss'
        ],
    },
    'qweb': [],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
