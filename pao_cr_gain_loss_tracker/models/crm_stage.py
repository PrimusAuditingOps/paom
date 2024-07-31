from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class CRMStage(models.Model):

    _inherit='crm.stage'

    is_lost = fields.Boolean('Is lost Stage?')