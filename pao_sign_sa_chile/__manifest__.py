# -*- coding: utf-8 -*-
{
    'name': 'PAO SIGN SA Chile',
    'version': '17.0.1.0.0',
    'author': 'samuel castro',
    'category': '',
    'website': 'https://paomx.com',
    'summary': """
        Chilean GLOBALG.A.P. service agreement (CERT-008) for the SA signature flow.
    """,
    'description': """
        Adds the CERT-008 "Acuerdo de Servicios de Programa de Certificación" for GLOBALG.A.P. registration
        numbers sent with the Chile country format. The form is built from the quotation lines of each
        organization / registration number: audit service, add-ons (catalog), fees and travel expenses.
    """,
    'depends': ['pao_sign_sa', 'pao_sign_ra', 'pao_chile_invoices'],
    'data': [
        # security
        'security/pao_sign_sa_chile_security.xml',
        'security/ir.model.access.csv',
        # reports
        'reports/sa_globalgap_cert008_chile.xml',
        # views
        'views/pao_sa_addon_views.xml',
        'views/product_template_views.xml',
        'views/sa_portal_template.xml',
    ],
    'license': 'LGPL-3',
}
