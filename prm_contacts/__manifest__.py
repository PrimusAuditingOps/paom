# -*- coding: utf-8 -*-
{
    'name': "PRM CONTACTS",

    'summary': """""",

    'description': """

    """,

    'author': "Omar Torres",
    'website': "http://proogeeks.com",

    # Categories can be used to filter modules in modules listing
    'category': 'Tools',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/prm_contact_type_line.xml',
        'views/prm_contact_type.xml',
        'views/prm_contact_commodity.xml',
        'views/prm_contact_shipper.xml',
    ],
    'license': 'LGPL-3',
}
