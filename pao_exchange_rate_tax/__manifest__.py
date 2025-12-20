{
    'name': 'PAO: Exchange Rate Tax Adjustment',
    'version': '17.0.1.0.0',
    'author': 'Port Cities',
    'category': 'Accounting',
    'website': 'https://www.portcities.net',
    'sequence': 1,
    'summary': """
        Proper handling of cash basis tax in exchange rate journal entries.
        Ensures tax amounts are fully recorded in tax accounts, not mixed with exchange rate accounts.
    """,
    'description': """
    v 1.0.0
        * Initial version for Odoo 17
        * Fixes tax calculation when payment triggers exchange rate journal entry
        * Ensures tax with exigibility 'Based on Payment' is fully recorded in tax accounts
        * Prevents tax amounts from being incorrectly allocated to exchange gain/loss accounts
        
    Preconditions for applying this module's logic:
        1. Payment triggers creation of exchange rate journal entry
        2. Tax exigibility is set to 'Based on Payment' (on_payment)
    """,
    'depends': [
        'account',
    ],
    'data': [
        "views/account_tax_views.xml"
    ],
    'assets': {
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
