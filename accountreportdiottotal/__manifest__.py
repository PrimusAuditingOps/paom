{
    'name': 'PAO: Account report Diot total',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Accounting/Accounting',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Add up the total amount of VAT in a row at the end of the report DIOT.
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'l10n_mx_reports'
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
