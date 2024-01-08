# -*- coding: utf-8 -*-
{
    'name':'PAO GLOBALGAP Fans',
    'version':'1.0',
    'author':'Samuel Castro',
    'category':'',
    'website':'https://paomx.com',
    'depends':['base','portal','website','servicereferralagreement',
    ],
    'data':[
        #security
        'security/ir.model.access.csv',
        #data
        'data/mail_template_data.xml',
        #demo
        #reports
        'reports/globagap_application_header_footer.xml',
        'reports/globalgap_application.xml',
        'reports/globalgap_certification_application.xml',
        #views
        'views/aplications_menus.xml',
        'views/sale_order.xml',
        'views/pao_globalgap_send_fans_request_view.xml',
        'views/fans_portal_template.xml',
        'views/fans_portal_template_production_site.xml',
        'views/fans_portal_template_product_information.xml',
    ],
    'css': [
        'static/src/css/pao_globalgap_fans.css',
    ],
    'application':'True',     
    
}