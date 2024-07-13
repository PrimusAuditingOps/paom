{
    'name': 'PAO: Commission Promotor',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Sale',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Sub-menu in the sales module that helps view and set commissions for people who
        They promote company audits to different clients.
    """,
    'description': """
    v 1.0
        Reviewer : Dwiki Adnan F. <dwiki@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'servicereferralagreement'
    ],
    'data': [
        'security/groups.xml',
        'security/ir_rules.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/commission_promoter_views.xml',
    ],
    'assets': {

    },
    'qweb': [
        
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
