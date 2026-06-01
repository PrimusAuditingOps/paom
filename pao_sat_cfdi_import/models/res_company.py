# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

  
    pao_l10n_mx_edi_certificate_ids = fields.One2many(
        comodel_name='pao.l10n_mx_edi.fiel',
        inverse_name='company_id',
        string='Fiel Certificates (MX)',
    )