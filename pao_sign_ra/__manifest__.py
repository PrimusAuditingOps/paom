{
    'name': 'PAO: Sign RA',
    'version': '17.0.0.1.0',
    'author': 'Manuel Uzueta',
    'website': 'https://www.paomx.com',
    'depends': [
        'auditconfirmation'
    ],
    'data' : [
        # 'security/groups.xml',
        # 'security/ir.model.access.csv',
        # 'security/ir_rules.xml',
        # 'views/res_partner.xml',
        'views/purchase_order.xml',
        'views/send_proposal_view_form.xml',
    ],

    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
