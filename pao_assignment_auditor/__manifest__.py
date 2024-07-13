{
    'name': 'PAO: Assignment Auditor',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Human Resource',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Its objective is the intelligent search for auditors.
        It takes into account the sales order information related to the current purchase order to,
        Depending on the audits (Products) sold, look for the best auditors
        (Suppliers) available. This tool considers some parameters, the same as
        can be configured to assign a certain percentage of relevance to the
        It's time to do the search.
    """,
    'description': """
    v 1.0
        Reviewer : Masoud AD. <masoud@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'base',
        'pao_base',
        'purchase',
        'base_geolocalize',
        'web',
        'servicereferralagreement',
        #'pao_assignment_in_house_auditor',
    ],
    'data' : [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/res_city_views.xml',
        'views/assignment_auditor_views.xml',
        'views/purchase_order_views.xml',
        'views/product_category_views.xml',
        'views/weighting_views.xml',
        'views/configuration_audit_quantity_views.xml',
        'views/configuration_audit_honorarium_views.xml',
        'views/assignment_auditor_qualification_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/pao_assignment_auditor/static/src/xml/**/*',
            '/pao_assignment_auditor/static/src/js/**/*',
        ],
    },
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}