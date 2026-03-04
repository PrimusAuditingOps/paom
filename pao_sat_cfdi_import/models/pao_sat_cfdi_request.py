
import pytz
from datetime import datetime, timedelta
from odoo import models, fields, api
from logging import getLogger
from odoo.exceptions import ValidationError
import base64
import zipfile
import io
from lxml import etree
from odoo.exceptions import UserError
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

    def request_download_package(self):
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
                for package in response["paquetes"]:
                    cfdi_package = self.env["pao.sat.cfdi.packages"].search([("name","=",str(package)),("sat_cfdi_request_id","=",self.id)])
                    if not cfdi_package:
                        self.env["pao.sat.cfdi.packages"].create(
                            {
                                "name": str(package),
                                "sat_cfdi_request_id": self.id
                            }
                        )
                self.write(
                    {
                        "verification_state": response["estado_solicitud"],
                        "verification_state_code": response["codigo_estatus"],
                        "message": response["mensaje"],
                        "total_cfdi": response["numero_cfdi"]
                    }
                )

    def download_package(self):
        self.ensure_one()
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        today = today.date()
        data = self.env["pao.l10n_mx_edi.fiel"].search([('date_end', '>=', today),('company_id', '=', self.env.company.id)], limit=1)
        if data:
            service = self.env["pao.sat.service"]
            for package in self.packages_ids:
                response = service.download_package(
                    data,
                    package.name,
                    self.requester_vat
                )
                
                if response:
                    package.write({"zip_file":response,"zip_file_name":package.name+".zip"})
    

    def read_file(self):
        for rec in self.packages_ids:
            if rec.zip_file:
                zip_bytes = base64.b64decode(rec.zip_file)
                file_zip = zipfile.ZipFile(io.BytesIO(zip_bytes))

                ns = {
                    'cfdi': 'http://www.sat.gob.mx/cfd/4',
                    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
                }

                for file_name in file_zip.namelist():

                    if not file_name.lower().endswith('.xml'):
                        continue

                    xml_bytes = file_zip.read(file_name)
                    root = etree.fromstring(xml_bytes)

                    _logger.error(file_name)
                    _logger.error(xml_bytes[:50])

                    name = root.xpath(
                        'string(.//tfd:TimbreFiscalDigital/@UUID)',
                        namespaces=ns
                    )

                    if self.env['pao.sat.cfdi.xml'].search([('name', '=', name)]):
                        continue

                    vendor_vat = root.xpath(
                        'string(.//cfdi:Emisor/@Rfc)',
                        namespaces=ns
                    )

                    vendor_name = root.xpath(
                        'string(.//cfdi:Emisor/@Nombre)',
                        namespaces=ns
                    )

                    customer_vat = root.xpath(
                        'string(.//cfdi:Receptor/@Rfc)',
                        namespaces=ns
                    )

                    customer_name = root.xpath(
                        'string(.//cfdi:Receptor/@Nombre)',
                        namespaces=ns
                    )

                    cfdi_date = root.xpath(
                        'string(/cfdi:Comprobante/@Fecha)',
                        namespaces=ns
                    )

                    total = root.xpath(
                        'string(/cfdi:Comprobante/@Total)',
                        namespaces=ns
                    )

                    subtotal = root.xpath(
                        'string(/cfdi:Comprobante/@SubTotal)',
                        namespaces=ns
                    )

                    currency = root.xpath(
                        'string(/cfdi:Comprobante/@Moneda)',
                        namespaces=ns
                    )

                    type_of_receipt = root.xpath(
                        'string(/cfdi:Comprobante/@TipoDeComprobante)',
                        namespaces=ns
                    )

                    concepts = root.xpath(
                        './/cfdi:Conceptos/cfdi:Concepto',
                        namespaces=ns
                    )

                    lines = []

                    for concept in concepts:

                        quantity = concept.get('Cantidad')
                        description = concept.get('Descripcion')
                        unit_value = concept.get('ValorUnitario')
                        amount = concept.get('Importe')
                        prod_serv_key = concept.get('ClaveProdServ')
                        unity_key = concept.get('ClaveUnidad')
                        unity = concept.get('Unidad')
                        tax_object = concept.get('ObjetoImp')

                        output_tax = concept.xpath(
                            './/cfdi:Traslado/@Importe',
                            namespaces=ns
                        )

                        withholding_tax = concept.xpath(
                            './/cfdi:Retencion/@Importe',
                            namespaces=ns
                        )

                        lines.append((0, 0, {
                            'prod_serv_key': prod_serv_key,
                            'description': description,
                            'quantity': float(quantity) if quantity else 0.0,
                            'unit_value': float(unit_value) if unit_value else 0.0,
                            'amount': float(amount) if amount else 0.0,
                            'unity_key': unity_key,
                            'unity': unity,
                            'tax_object': tax_object,
                            'output_tax': float(output_tax[0]) if output_tax else 0.0,
                            'withholding_tax': float(withholding_tax[0]) if withholding_tax else 0.0,
                        }))
                    
                    date = False

                    if cfdi_date:
                        date = datetime.strptime(cfdi_date, "%Y-%m-%dT%H:%M:%S")
                    
                    xml_text = xml_bytes.lstrip(b'\xef\xbb\xbf').decode('utf-8')
                    parser = etree.XMLParser(remove_blank_text=True)
                    root = etree.fromstring(xml_bytes, parser)

                    xml_text = etree.tostring(
                        root,
                        pretty_print=True,
                        encoding='unicode'
                    )
                    
                    self.env['pao.sat.cfdi.xml'].create(
                        {
                            'name': name,
                            'vendor_vat': vendor_vat,
                            'vendor_name': vendor_name,
                            'customer_vat': customer_vat,
                            'customer_name': customer_name,
                            'pao_line_ids': lines,
                            'cfdi_date': date,
                            'total': float(total) if total else 0.0,
                            'subtotal': float(subtotal) if subtotal else 0.0,
                            'currency': currency,
                            'xml_text': xml_text,
                            'type_of_receipt': type_of_receipt,
                            'xml_files': base64.b64encode(xml_bytes),
                            'file_name': name + '.xml',
                        }
                    )




