from odoo import models
from odoo.tools.translate import _



class MexicanAccountReportCustomHandler(models.AbstractModel):
    _inherit = 'l10n_mx.report.handler'

    def _custom_line_postprocessor(self, report, options, lines, warnings=None):
        lines = super(MexicanAccountReportCustomHandler, self)._custom_line_postprocessor(
            report, options, lines, warnings)
    
        sumtotaliva = 0
        totadiot = []
    
        for reg in lines:
            if reg.get('level') == 3:
                array_total = reg.get('columns')
                objtotal = array_total[5]
                sumtotaliva += int(round(objtotal.get('no_format'), 0)) 
    
        if options.get("headers") == None: 
            totadiot.append({
                    'id': 'sumtotal_diot',
                    'name': '',
                    'columns': [{'name': ''},{'name': ''},{'name': ''},{'name': ''},{'name': ''},{
                        'name': report.format_value(options, sumtotaliva),
                        'no_format': sumtotaliva,
                    }],
                    'level': 2
                })
            lines += totadiot
    
        return lines
