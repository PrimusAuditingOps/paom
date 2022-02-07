from odoo import models
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)

class l10nMxAccountDiotInherit(models.AbstractModel):
    _inherit= "l10n_mx.account.diot"

    def _get_lines(self, options, line_id=None):
        res = super(l10nMxAccountDiotInherit, self)._get_lines(options,line_id)
        
        sumtotaliva = 0
        totadiot = []

        for reg in res:
            if reg.get('level') == 2:
                array_total = reg.get('columns')
                objtotal = array_total[5]
                sumtotaliva += int(round(objtotal.get('name'), 0)) 

        if options.get("headers") == None: 
            totadiot.append({
                    'id': 'sumtotal_diot',
                    'name': '',
                    'columns': [{'name': ''},{'name': ''},{'name': ''},{'name': ''},{'name': ''},{'name': sumtotaliva}],
                    'level': 2
                })
            res += totadiot

        return res