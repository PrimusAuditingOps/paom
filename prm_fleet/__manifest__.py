# -*- coding: utf-8 -*-
{
    'name': "PRM FLEET",

    'summary': """""",

    'description': """

    """,

    'author': "otorresmx (otorres@proogeeks.com)",
    'website': "http://proogeeks.com",

    # Categories can be used to filter modules in modules listing
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'fleet'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_vehicle.xml',
    ]
}

