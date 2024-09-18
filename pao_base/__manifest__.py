{
    'name': 'PAO: Base',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Base',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Base general changes
    """,
    'description': """
    v 1.0
        Author : Masoud AD. <masoud@portcities.net>\n
        * Set PAO modules in APP as default\n
        * Add res.city as City to use in addresses
    """,
    'depends': [
        'base',
        'contacts',
        'l10n_mx_edi'
    ],
    'data' : [
        'security/ir.model.access.csv',
        'views/res_city_views.xml',
        'views/res_country_views.xml',
        'views/res_partner_views.xml',
        'views/ir_module_views.xml',
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
