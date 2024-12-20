from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class ComisionpromotoresPromotor(models.Model):

    _inherit='comisionpromotores.promotor'
    
    pao_lead_ids = fields.One2many(
        comodel_name='crm.lead',
        inverse_name='pao_consultant_id',
        string='Leads',
    )


    