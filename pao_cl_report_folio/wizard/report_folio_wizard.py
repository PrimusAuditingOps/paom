import json

from odoo import api, fields, models


class ReportFolioWizard(models.TransientModel):
    """ Asks for an optional folio, then prints the report given in the context
    (``default_report_xmlid``) for the selected records.

    How a report uses it: its print-menu entry is an ir.actions.act_window on this
    wizard instead of the report itself, and its ``_get_report_values`` reads
    ``data['res_ids']`` (the records) and ``data.get('folio')`` (blank = no folio).
    The folio is only used for that print; nothing is kept (transient record).
    """
    _name = 'pao.cl.report.folio.wizard'
    _description = 'Folio para reportes PDF (Chile)'

    folio = fields.Char(string='Folio')
    report_xmlid = fields.Char(required=True)
    res_model = fields.Char(required=True)
    # Selected record ids as JSON text (a Json field has no widget to sit in the form).
    res_ids = fields.Text()

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        context = self.env.context
        if 'res_model' in fields_list:
            values.setdefault('res_model', context.get('active_model'))
        if 'res_ids' in fields_list:
            values.setdefault('res_ids', json.dumps(context.get('active_ids') or []))
        return values

    def action_print(self):
        self.ensure_one()
        records = self.env[self.res_model].browse(json.loads(self.res_ids or '[]'))
        data = {'res_ids': records.ids}
        folio = (self.folio or '').strip()
        if folio:
            data['folio'] = folio
        action = self.env.ref(self.report_xmlid).report_action(records, data=data, config=False)
        action['close_on_report_download'] = True
        return action
