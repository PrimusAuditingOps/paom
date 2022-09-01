# -*- coding: utf-8 -*-
{
    'name': 'PAO Assignment Auditor',
    'version': '1.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'depends': ['base','purchase','base_geolocalize','web','servicereferralagreement',
    ],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        # data
        # demo
        # reports
        # views
        'views/res_partner.xml',
        'views/assignment_auditor.xml',
        'views/purchase_order.xml',
        'views/product_category.xml',
        'views/weighting.xml',
        'views/configuration_audit_quantity.xml',
        'views/configuration_audit_honorarium.xml',
        'views/assignment_auditor_qualification.xml',
        'views/assets.xml',
        
    ],
    'qweb': [
        'static/src/xml/popup_assignment_auditor.xml',
    ],
}
