from odoo import models, api

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    @api.model
    def search_read(self, domain, fields, offset=0, limit=None, order=None):
        context = self.env.context
        if context.get('sudo'):
            self = self.sudo()
        return super(DiscussChannel, self).search_read(domain, fields, offset=offset, limit=limit, order=order)
