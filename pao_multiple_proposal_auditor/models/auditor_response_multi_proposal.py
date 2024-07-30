from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from logging import getLogger
from datetime import datetime
from werkzeug.urls import url_join
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class auditor_response_multi_proposal(models.Model):
    _name = 'auditor.response.multi.proposal'
    _description = 'Auditor response multi-proposal'


    auditor_id = fields.Many2one('res.partner', string="Auditor",)

    status = fields.Selection(
        selection=[
            ('not_confirmed', "Not confirmed"),
            ('accepted', "Accepted"),
            ('declined', "Declined"),
        ],
        default='not_confirmed',
        string="Status", 
        readonly=True, 
        copy=False,
    )

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase order',
        ondelete='cascade',
    )