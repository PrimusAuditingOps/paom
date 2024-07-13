{
    'name': 'PAO: Sign Templates',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Sale',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Add two email templates when sending a document to be signed (Application of signature)
        and also establishes a number of days in which it will be sent automatically gives
        the customer a daily reminder that their signature is required.
    """,
    'description': """
    v 1.0
        Reviewer : Dwiki Adnan F. <dwiki@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'sign'
    ],
    'data': [
        #'data/cron_data.xml',
        'views/sign_send_request_views.xml',
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
