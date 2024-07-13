{
    'name': 'PAO: Audit confirmation',
    'version': '17.0.0.2.0',
    'author': 'Port Cities',
    'category': 'Purchase',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        - Add button to change the status of an audit (purchase order).
        - Add button box showing the audit confirmation status.
        - Add button that shows the history of audit statuses.
        - Add An email availability confirmation template.
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'base',
        'portal',
        'servicereferralagreement'
    ],
    'data' : [
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'data/mail_template_data.xml',
        'views/auditconfirmation.xml',
        'views/purchase_order_views.xml',
        'views/audit_state.xml',
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
