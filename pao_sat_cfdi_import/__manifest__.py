{
    'name': 'PAO SAT CFDI Import',
    'version': '17.0.0.1.0',
    'author': 'Samuel Castro',
    'sequence': 1,
    'summary': """
        
    """,
    'description': """
   
    """,
    'depends': [
        'account','l10n_mx_edi'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sat_cfdi_request.xml',
        #'data/ir_cron.xml',
    ],
    'assets': {

    },
    'qweb': [
        
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
