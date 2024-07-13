{
    'name': 'PAO: Audit assignment',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Human Resource',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Its objective is to validate that an auditor is suitable to perform an audit service.
        It reviews each of the lines of a purchase order
        when saving the information and if it finds a product
        that is not on the auditor's list of approved products,
        it throws an error message.
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'base',
        'purchase',
        'auditordaysoff'
    ],
    'data' : [
        'views/res_partner.xml',
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