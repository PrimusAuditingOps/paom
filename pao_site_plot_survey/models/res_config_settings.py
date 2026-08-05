# -*- coding: utf-8 -*-
from odoo import fields, models

from .ir_config_parameter import GOOGLE_MAPS_API_KEY_PARAM


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pao_google_maps_api_key = fields.Char(
        string='Google Maps API Key',
        config_parameter=GOOGLE_MAPS_API_KEY_PARAM,
    )
