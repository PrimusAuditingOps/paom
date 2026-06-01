# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

  
    sat_cfdi_xml_id = fields.Many2one(
        'pao.sat.cfdi.xml',
        string='SAT CDFI XML',
        ondelete='set null'
    )