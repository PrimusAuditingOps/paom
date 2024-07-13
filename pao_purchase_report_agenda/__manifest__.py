{
    'name': 'PAO: Purchase report agenda',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Purchase',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Adds new information fields to the native Odoo purchasing report.
        Fields referring to purchase orders assigned to auditors (Suppliers). As
        For example, it allows you to know how many audits an auditor is in as a Shadow (Apprentice)
        or assessment (Evaluated).
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'pao_base',
        'purchase',
        'servicereferralagreement',
        'auditconfirmation'
    ],
    'data' : [
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
