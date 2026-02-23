
import pytz
from datetime import datetime, timedelta
from odoo import models, fields, api
from ..services.sat_descarga_service import SatDescargaMasivaService
from logging import getLogger
from odoo.exceptions import ValidationError

_logger = getLogger(__name__)

class SATCFDIRequest(models.Model):
    _name = "pao.sat.cfdi.request"
    _description = "CFDI package requests"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    cfdi_type = fields.Selection(
        selection=[
            ('I', "Recibidos"),  
        ],
        string="Sense of CFDI",
        default='I',
    )
    requester_vat = fields.Char(
        string="Requester VAT",

    )
    start_date = fields.Date(
        string="Start Date",
        required=True,
    )
    end_date = fields.Date(
        string="End Date",
        required=True,
    )
    receiver_rfc = fields.Char(
        string="Receiver VAT",
    )
    request_id = fields.Char(
        string="Request ID",
    )
    verification_state = fields.Char(
        string="Verification State",
    )
    message = fields.Char(
        string="Message",
    )
    verification_state_code = fields.Char(
        string="Verification State Code",
    )

    total_cfdi = fields.Integer(
        string="Total CFDI",
    )

    def download_package(self):
        self.ensure_one()
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        today = today.date()
        data = self.env["l10n_mx_edi.certificate"].search([('date_start', '>=', today), ('date_end', '<=', today)], limit=1)
        _logger.error(data)
        if data:
            response = SatDescargaMasivaService.auth_sat(
                "",
                data.content,
                data.key,
                data.password
            )
            raise ValidationError(response)



    