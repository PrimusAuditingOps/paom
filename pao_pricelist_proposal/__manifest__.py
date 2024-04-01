{
    "name": "PAO Pricelist Proposal",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "https://paomx.com",
    "depends": ["base", "product", "sale"],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        
        'data/mail_template.xml',
        'data/pricelist_template.xml',
        'views/proposal_agreement_report.xml',
        
        'views/pricelist_portal_template.xml',
        'views/proposal_terms_schemes_views.xml',
        'views/proposal_item_views.xml',
        'views/product_pricelist_form_inherit.xml',
        'views/pao_pricelist_proposal_view_form.xml',
        'views/send_proposal_view_form.xml',
        'views/hr_employeee_form_inherit.xml',
    ],
}