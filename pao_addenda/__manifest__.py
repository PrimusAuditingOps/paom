# -*- coding: utf-8 -*-
{
    'name': 'PAO Addenda',
    'version': '17.0.1.0.0',
    'author': 'PAO',
    'category': 'Accounting/Localizations/EDI',
    'website': 'https://paomx.com',
    'summary': 'Addenda CFDI para Hortifrut (folio de orden de compra por factura)',
    'description': """
Agrega el folio de orden de compra a la factura de cliente y lo incluye en la
Addenda del CFDI de los contactos que tengan asignada la Addenda Hortifrut.
Ver CONTEXT.md.
    """,
    'depends': ['l10n_mx_edi'],
    'data': [
        # data
        'data/addenda_hortifrut.xml',
        # views
        'views/account_move_views.xml',
    ],
    'license': 'LGPL-3',
}
