
import pytz
from datetime import datetime, timedelta
from odoo import models, fields, api
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

    packages_ids= fields.One2many(
        'pao.sat.cfdi.packages',
        inverse_name='sat_cfdi_request_id',
        string='Packages'
    )

    def download_package(self):
        self.ensure_one()
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        today = today.date()
        data = self.env["pao.l10n_mx_edi.fiel"].search([('date_end', '>=', today),('company_id', '=', self.env.company.id)], limit=1)
        if data:
            service = self.env["pao.sat.service"]
            response = service.request_download(
                data,
                self.start_date,
                self.end_date
            )
            if response:
                self.write(
                    {
                        "request_id": response["id_solicitud"],
                        "verification_state_code": response["cod_estatus"],
                        "message": response["mensaje"],
                        "requester_vat": response["rfc_solicitante"]
                    }
                )

    def request_status(self):
        self.ensure_one()
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        today = today.date()
        data = self.env["pao.l10n_mx_edi.fiel"].search([('date_end', '>=', today),('company_id', '=', self.env.company.id)], limit=1)
        if data:
            service = self.env["pao.sat.service"]
            response = service.request_status(
                data,
                self.request_id,
                self.requester_vat
            )
            if response:
                #for package in response["paquetes"]:
                #    cfdi_package = self.self.env["pao.sat.cfdi.packages"].search([("name","=",package),("sat_cfdi_request_id","=",self.id)])
                #    if not cfdi_package:
                #        self.env["pao.sat.cfdi.packages"].create(
                #            {
                #                "name": package,
                #                "sat_cfdi_request_id": self.id
                #            }
                #        )
                self.write(
                    {
                        "verification_state": response["estado_solicitud"],
                        "verification_state_code": response["codigo_estatus"],
                        "message": response["mensaje"],
                        "total_cfdi": response["numero_cfdi"]
                    }
                )


    