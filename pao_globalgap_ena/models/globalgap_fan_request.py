from datetime import datetime, timedelta
from odoo import fields, models, api, _



class GlobalGAPFanRequest(models.Model):
    _inherit = 'pao.globalgap.fans.request'

    pao_ena_ids = fields.One2many(
        'ena.solicitud', 
        inverse_name='request_fan_id',                                
        string='Auditorias no anunciadas'
    )