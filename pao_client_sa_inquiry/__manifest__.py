{
    "name": "PAO Client SA Inquiry",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "",
    "depends": ["contacts","pao_sign_sa"],
    'data': [
        'views/res_partner_inherit.xml',
        'views/portal_sa_view.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}