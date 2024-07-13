{
    'name': 'PAO: Digital Services Catalog',
    'version': '17.0.0.1.0',
    'author': 'Port Cities',
    'category': 'Website',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Add a new section called “Services” to the company's website. Which shows a digital catalog
        of all the services offered by the company in the form of a flipbook.
    """,
    'description': """
    v 1.0
        Reviewer : Dwiki Adnan F. <dwiki@portcities.net>\n
        * Migrated from v14.\n
    """,
    'depends': [
        'sale', 'website'
    ],
    'data' : [
        'views/views.xml'
    ],
    'assets': {
        'web.report_assets_common': [
        ],
        'web.assets_backend': [
        ],
    },
    'qweb': [],
    'installable': True,
    'application' : False,
    'auto_install' : False,
    'license': 'LGPL-3',
}
