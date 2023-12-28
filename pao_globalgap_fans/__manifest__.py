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
        #views
        'views/aplications_menus.xml',
        'views/sale_order.xml',
        'views/pao_globalgap_send_fans_request_view.xml',
        'views/fans_portal_template.xml',
        'views/fans_portal_template_production_site.xml',
    ],
    'application':'True',     
    
}