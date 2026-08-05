# -*- coding: utf-8 -*-
from odoo import api, models

GOOGLE_MAPS_API_KEY_PARAM = 'pao_site_plot_survey.google_maps_api_key'


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def get_pao_google_maps_api_key(self):
        """Whitelisted read of the Maps API key: ir.config_parameter is
        group_system-gated by default and a salesperson wouldn't otherwise
        be able to fetch it to bootstrap the map widget."""
        return self.sudo().get_param(GOOGLE_MAPS_API_KEY_PARAM, default='')
