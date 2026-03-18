
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

    _sql_constraints = [
        (
            'pao_sat_cfdi_request_unique',
            'unique(cfdi_type, start_date, end_date, company_id)',
            'A CFDI request with these dates already exists.'
        )
    ]
    
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
    request_state_code = fields.Char(
        string="Request State Code",
    )
    message = fields.Char(
        string="Message",
    )
    verification_state_code = fields.Char(
        string="Verification State Code",
    )
    verification_state = fields.Char(
        string="Verification State",
    )

    total_cfdi = fields.Integer(
        string="Total CFDI",
    )

    packages_ids= fields.One2many(
        'pao.sat.cfdi.packages',
        inverse_name='sat_cfdi_request_id',
        string='Packages'
    )
    request_state = fields.Selection(
        selection=[
            ('error', "Error"),  
            ('progress', "In Progress"), 
            ('done', "Done"), 
        ],
        string="Request State",
        default='progress',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, 
        index=True,
        default=lambda self: self.env.company
    )
    xml_ids= fields.One2many(
        'pao.sat.cfdi.xml',
        inverse_name='sat_cfdi_request_id',
        string='XML'
    )

    def create_request_download(self):
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        yesterday = today - timedelta(days=1)
        record = self.env["pao.sat.cfdi.request"].search([("start_date","=",yesterday),("end_date","=",yesterday),("company_id","=",1)])
        if not record:
            rec_id = self.env["pao.sat.cfdi.request"].create(
                {
                    "start_date": yesterday,
                    "end_date": yesterday,
                    "company_id": 1,
                }
            )
            data = self.env["pao.l10n_mx_edi.fiel"].search([('date_end', '>=', today),('company_id', '=', 1)], limit=1)
            if data:
                service = self.env["pao.sat.service"]
                response = service.request_download(
                    data,
                    rec_id.start_date,
                    rec_id.end_date
                )
                if response:
                    rec_id.write(
                        {
                            "request_id": response["id_solicitud"],
                            "request_state_code": response["cod_estatus"],
                            "message": response["mensaje"],
                            "requester_vat": response["rfc_solicitante"]
                        }
                    )
    """
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
    """
    def request_status(self):
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        today = today.date()

        records = self.env["pao.sat.cfdi.request"].search(
            [
                ('request_state_code', '=', "5000"),
                ('verification_state_code', '!=', "5000")
            ]
        )
        for rec in records:
            data = self.env["pao.l10n_mx_edi.fiel"].search([('date_end', '>=', today),('company_id', '=', rec.company_id.id)], limit=1)
            if data:
                service = self.env["pao.sat.service"]
                response = service.request_status(
                    data,
                    rec.request_id,
                    rec.requester_vat
                )
                if response:
                    if response["codigo_estatus"] == "5000":
                        for package in response["paquetes"]:
                            cfdi_package = self.env["pao.sat.cfdi.packages"].search([("name","=",str(package)),("sat_cfdi_request_id","=",rec.id)])
                            if not cfdi_package:
                                response_download = service.download_package(
                                    data,
                                    str(package),
                                    rec.requester_vat
                                )
                                if response_download:
                                    self.env["pao.sat.cfdi.packages"].create(
                                        {
                                            "name": str(package),
                                            "zip_file":response_download,
                                            "zip_file_name":package+".zip",
                                            "sat_cfdi_request_id": rec.id
                                        }
                                    )

                        rec.read_file()
                    rec.write(
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
        for request_id in self:
            for rec in request_id.packages_ids:
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

                        

                        lines = []

                       
                        type_receipt = root.xpath(
                            'string(/cfdi:Comprobante/@TipoDeComprobante)',
                            namespaces=ns
                        )
                        #exchange_rate
                        customer_tax_regime = root.xpath(
                            'string(.//cfdi:Receptor/@RegimenFiscalReceptor)',
                            namespaces=ns
                        )
                        vendor_tax_regime = root.xpath(
                            'string(.//cfdi:Emisor/@RegimenFiscal)',
                            namespaces=ns
                        )

                        cfdi_use = root.xpath(
                            'string(.//cfdi:Receptor/@UsoCFDI)',
                            namespaces=ns
                        )
                        payment_method = root.xpath(
                            'string(/cfdi:Comprobante/@MetodoPago)',
                            namespaces=ns
                        )
                        method_of_payment = root.xpath(
                            'string(/cfdi:Comprobante/@FormaPago)',
                            namespaces=ns
                        )
                        export = root.xpath(
                            'string(/cfdi:Comprobante/@Exportacion)',
                            namespaces=ns
                        )

                        concepts = root.xpath(
                            './/cfdi:Conceptos/cfdi:Concepto',
                            namespaces=ns
                        )

                        for concept in concepts:
                            
                            traslados = concept.xpath(
                                './/cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado',
                                namespaces=ns
                            )

                            retenciones = concept.xpath(
                                './/cfdi:Impuestos/cfdi:Retenciones/cfdi:Retencion',
                                namespaces=ns
                            )
                            _logger.error(traslados)
                            _logger.error(retenciones)

                            for traslado in traslados:
                                impuesto = traslado.get('Impuesto')
                                base = traslado.get('Base')
                                tipo_factor = traslado.get('TipoFactor')
                                tasa = traslado.get('TasaOCuota')
                                importe = traslado.get('Importe')

                                _logger.error(base)

                            for retencion in retenciones:
                                impuesto = retencion.get('Impuesto')
                                base = retencion.get('Base')
                                tasa = retencion.get('TasaOCuota')
                                importe = retencion.get('Importe')

                                _logger.error(base)

                     

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
                                'sat_cfdi_request_id': request_id.id,
                                'export': export,
                                'payment_method': payment_method,
                                'cfdi_use': cfdi_use,
                                'vendor_tax_regime': vendor_tax_regime,
                                'customer_tax_regime': customer_tax_regime,
                                'type_receipt': type_receipt,
                                'method_of_payment': method_of_payment,
                            }
                        )




