from odoo import api, exceptions, fields, models, _


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def action_download_attachment(self):
        tab_id = []
        for attachment in self:
            tab_id.append(attachment.id)
        url = '/web/binary/download_document?tab_id=%s' % tab_id
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }