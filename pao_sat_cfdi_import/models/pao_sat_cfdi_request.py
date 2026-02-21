from odoo import models, fields, api
from ..services.sat_descarga_service import SatDescargaMasivaService

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



    