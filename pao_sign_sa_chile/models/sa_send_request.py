# -*- coding: utf-8 -*-
from odoo import models


class SASendRequest(models.TransientModel):
    _inherit = 'sa.send.request'

    def _is_globalgap_format_available(self):
        return super()._is_globalgap_format_available() or self.country_format == 'CL'
