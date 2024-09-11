# -*- coding: utf-8 -*-
{
    'name':'PAO GLOBALGAP Fans',
    'version': '17.0.0.1.0',
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
        'data/signature_template_data.xml',
        #demo
        #reports
        'reports/globagap_application_header_footer.xml',
        'reports/globalgap_application.xml',
        #views
        'views/globalgap_application_portal_view.xml',
        'views/globalgap_certification_application.xml',
        'views/aplications_menus.xml',
        'views/sale_order.xml',
        'views/pao_globalgap_send_fans_request_view.xml',
        'views/fans_portal_template.xml',
        'views/fans_portal_template_production_site.xml',
        'views/fans_portal_template_product_information.xml',
    ],
    'css': [
        '/pao_globalgap_fans/static/src/css/pao_globalgap_fans.css',
        'https://api.mapbox.com/mapbox-gl-js/v2.9.1/mapbox-gl.css',
        '/pao_globalgap_fans/static/src/css/chosen.css',
        'https://unpkg.com/gridjs/dist/theme/mermaid.min.css',
        #'https://cdnjs.cloudflare.com/ajax/libs/jquery-datetimepicker/2.3.7/jquery.datetimepicker.min.css',
    ],
    'assets': {
        'web.assets_frontend': [
            #'https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js',
            #'https://cdnjs.cloudflare.com/ajax/libs/jquery-datetimepicker/2.5.20/jquery.datetimepicker.full.min.js',
            '/pao_globalgap_fans/static/src/js/pao_globalgap_fans.js',
            '/pao_globalgap_fans/static/src/js/pao_globalgap_production_site.js',
            '/pao_globalgap_fans/static/src/js/pao_globalgap_product_information.js',
            '/pao_globalgap_fans/static/src/js/chosen.jquery.js',
            'https://api.mapbox.com/mapbox-gl-js/v2.9.1/mapbox-gl.js',
            'https://api.mapbox.com/mapbox-gl-js/v2.9.1/mapbox-gl.js',
            'https://unpkg.com/gridjs/dist/gridjs.umd.js',
            '/pao_globalgap_fans/static/src/css/pao_globalgap_fans.css',
            'https://api.mapbox.com/mapbox-gl-js/v2.9.1/mapbox-gl.css',
            '/pao_globalgap_fans/static/src/css/chosen.css',
            'https://unpkg.com/gridjs/dist/theme/mermaid.min.css',
            
        ],
    },
    'application':'True',     
    'license': 'LGPL-3',
    
}