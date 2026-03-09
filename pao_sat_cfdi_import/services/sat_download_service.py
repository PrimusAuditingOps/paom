#import base64
#import uuid
#import pytz
#from datetime import datetime, timedelta
#from lxml import etree
#from zeep import Client
#from cryptography.hazmat.primitives.serialization import load_der_private_key
#from cryptography.hazmat.primitives import hashes
#from cryptography.hazmat.primitives.asymmetric import padding
#from cryptography import x509

import base64
import uuid
import pytz
import requests
import datetime
import xmlsec
import tempfile
import subprocess
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from lxml import etree
from zeep import Client
from zeep.transports import Transport
from requests import Session
from OpenSSL import crypto
from logging import getLogger
from datetime import datetime, timedelta, timezone
from odoo import models
from odoo.exceptions import UserError




_logger = getLogger(__name__)

class SATDownloadService(models.AbstractModel):
    _name = "pao.sat.service"

    def _prepare_key_and_cert(self, data):

        # Decodificar base64
        cer_der = base64.b64decode(data.content)
        key_der = base64.b64decode(data.key)
        password = data.password

        # Crear archivos temporales
        cer_der_file = tempfile.NamedTemporaryFile(delete=False)
        key_der_file = tempfile.NamedTemporaryFile(delete=False)

        cer_der_file.write(cer_der)
        key_der_file.write(key_der)

        cer_der_file.close()
        key_der_file.close()

        # Convertir CER DER → PEM
        cer_pem_file = tempfile.NamedTemporaryFile(delete=False)
        subprocess.run([
            "openssl",
            "x509",
            "-inform", "DER",
            "-outform", "PEM",
            "-in", cer_der_file.name,
            "-out", cer_pem_file.name
        ])

        # Convertir KEY DER → PEM desencriptado
        key_pem_file = tempfile.NamedTemporaryFile(delete=False)
        subprocess.run([
            "openssl",
            "pkcs8",
            "-inform", "DER",
            "-in", key_der_file.name,
            "-passin", f"pass:{password}",
            "-topk8",
            "-nocrypt",
            "-outform", "PEM",
            "-out", key_pem_file.name
        ], check=True)

        return cer_pem_file.name, key_pem_file.name

    def _create_timestamp(self):
        created = datetime.now(timezone.utc)
        expires = created + timedelta(minutes=5)

        return (
            created.strftime('%Y-%m-%dT%H:%M:%SZ'),
            expires.strftime('%Y-%m-%dT%H:%M:%SZ')
        )
        
        """
        requested_tz = pytz.timezone('America/Mexico_City')
        created = requested_tz.fromutc(datetime.utcnow())
        expires = created + timedelta(minutes=5)

        return (
            created.strftime('%Y-%m-%dT%H:%M:%SZ'),
            expires.strftime('%Y-%m-%dT%H:%M:%SZ')
        )
        """

    def _build_envelope(self, cert_b64):

        created, expires = self._create_timestamp()
        token_id = f"uuid-{uuid.uuid4()}-4"

        NSMAP = {
            'u': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd',
            's': 'http://schemas.xmlsoap.org/soap/envelope/',
            #'o': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
        }

        envelope = etree.Element(
            '{http://schemas.xmlsoap.org/soap/envelope/}Envelope',
            nsmap=NSMAP
        )

        header = etree.SubElement(
            envelope,
            '{http://schemas.xmlsoap.org/soap/envelope/}Header'
        )

        security = etree.SubElement(
            header,
            '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Security',
            {
                '{http://schemas.xmlsoap.org/soap/envelope/}mustUnderstand': '1',
            },
             nsmap={
                'o': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
            }
        )

        timestamp = etree.SubElement(
            security,
            '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Timestamp',
            {
                '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Id': '_0'
            }
        )

        etree.SubElement(
            timestamp,
            '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Created'
        ).text = created

        etree.SubElement(
            timestamp,
            '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Expires'
        ).text = expires

        binary_token = etree.SubElement(
            security,
            '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken',
            {
                '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Id': token_id,
                'ValueType': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3',
                'EncodingType': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary',
            }
        )

        binary_token.text = cert_b64.replace("\n", "")

        body = etree.SubElement(
            envelope,
            '{http://schemas.xmlsoap.org/soap/envelope/}Body'
        )

        etree.SubElement(
            body,
            '{http://DescargaMasivaTerceros.gob.mx}Autentica'
        )

        return envelope, token_id

    def _sign(self, envelope, certificate, token_id):

        #signature_node = xmlsec.template.create(
        #    envelope,
        #    xmlsec.Transform.EXCL_C14N,
        #    xmlsec.Transform.RSA_SHA1
        #)
        signature_node = xmlsec.template.create(
            envelope,
            xmlsec.Transform.EXCL_C14N,
            xmlsec.Transform.RSA_SHA1
        )

        key_info = xmlsec.template.ensure_key_info(signature_node)

        str_node = etree.SubElement(
            key_info,
            '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}SecurityTokenReference'
        )

        etree.SubElement(
            str_node,
            '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Reference',
            ValueType='http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3',
            URI=f'#{token_id}'
        )

        # Insertar Signature dentro de Security
        security_node = envelope.find(
            './/{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Security'
        )
        security_node.append(signature_node)

        # Registrar Id
        xmlsec.tree.add_ids(envelope, ["Id"])

        # Verificar que los nodos existan
       

        # Crear referencia
        ref = xmlsec.template.add_reference(
            signature_node,
            xmlsec.Transform.SHA1,
            uri='#_0'
        )

        xmlsec.template.add_transform(ref, xmlsec.Transform.EXCL_C14N)
        
        

        # Obtener PEM ya convertido correctamente
        cer_path, key_path = self._prepare_key_and_cert(certificate)

        
        # Cargar key PEM limpia
        key = xmlsec.Key.from_file(key_path, xmlsec.KeyFormat.PEM)
        key.load_cert_from_file(cer_path, xmlsec.KeyFormat.PEM)

        ctx = xmlsec.SignatureContext()
        ctx.key = key
        # Firmar
        ctx.sign(signature_node)

        return envelope

    def _auth(self,certificate):

        cert_b64 = base64.b64encode(
            base64.b64decode(certificate.content)
        ).decode()

        envelope, token_id = self._build_envelope(cert_b64)
        signed_envelope = self._sign(envelope, certificate, token_id)
        _logger.error(etree.tostring(signed_envelope,encoding="utf-8"))
        response = requests.post(
            "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc",
            data=etree.tostring(signed_envelope),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '"http://DescargaMasivaTerceros.gob.mx/IAutenticacion/Autentica"'
            }
        )
        _logger.error(response.content)
        
        return self._parse_auth_response(response.content)

    def _parse_auth_response(self, xml_response):

        root = etree.fromstring(xml_response)

        ns = {
            's': 'http://schemas.xmlsoap.org/soap/envelope/',
            'd': 'http://DescargaMasivaTerceros.gob.mx'
        }

        fault = root.find('.//s:Fault', namespaces=ns)
        if fault is not None:
            fault_string = fault.findtext('faultstring')
            raise UserError(f"Error SAT: {fault_string}")

        token_node = root.find('.//d:AutenticaResult', namespaces=ns)

        if token_node is None or not token_node.text:
            raise UserError("No se recibió token de autenticación del SAT.")

        token = token_node.text.strip()

        return {
            "success": True,
            "token": token
        }

    def request_download(self, certificate, start_date, end_date):
        data = ""
        url = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc"

        auth_result = self._auth(certificate)

        if not auth_result["success"]:
            raise UserError("No fue posible autenticarse con el SAT")

        token = auth_result["token"]

        fecha_inicio_dt = datetime.combine(start_date, datetime.min.time())
        fecha_fin_dt = datetime.combine(end_date, datetime.max.time().replace(microsecond=0))

        fecha_inicio_str = fecha_inicio_dt.strftime('%Y-%m-%dT%H:%M:%S')
        fecha_fin_str = fecha_fin_dt.strftime('%Y-%m-%dT%H:%M:%S')

        solicitud = etree.Element(
            "solicitud",
            EstadoComprobante="Vigente",
            FechaInicial=fecha_inicio_str,
            FechaFinal=fecha_fin_str,
            TipoSolicitud="CFDI",
            RfcReceptor=certificate.vat
        )
        signature_node = xmlsec.template.create(
            solicitud,
            xmlsec.Transform.C14N,      
            xmlsec.Transform.RSA_SHA1
        )
        solicitud.insert(0, signature_node)

        ref = xmlsec.template.add_reference(
            signature_node,
            xmlsec.Transform.SHA1,
            uri=""
        )

        cer_bytes = base64.b64decode(certificate.content)

        cert = x509.load_der_x509_certificate(cer_bytes, default_backend())

        issuer_name = cert.issuer.rfc4514_string()
        serial_number = str(cert.serial_number)


        xmlsec.template.add_transform(ref, xmlsec.Transform.ENVELOPED)

        key_info = xmlsec.template.ensure_key_info(signature_node)
        x509_data = xmlsec.template.add_x509_data(key_info)

        issuer_serial = xmlsec.template.x509_data_add_issuer_serial(x509_data)

        issuer_name_node = xmlsec.template.x509_issuer_serial_add_issuer_name(issuer_serial)
        issuer_name_node.text = issuer_name

        serial_node = xmlsec.template.x509_issuer_serial_add_serial_number(issuer_serial)
        serial_node.text = serial_number

        xmlsec.template.x509_data_add_certificate(x509_data)

        xmlsec.tree.add_ids(solicitud, ["Id"])

        cer_path, key_path = self._prepare_key_and_cert(certificate)

        key = xmlsec.Key.from_file(key_path, xmlsec.KeyFormat.PEM)
        key.load_cert_from_file(cer_path, xmlsec.KeyFormat.PEM)

        ctx = xmlsec.SignatureContext()
        ctx.key = key

        ctx.sign(signature_node)

        c14n_method = signature_node.find(
            ".//{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod"
        )
        c14n_method.set(
            "Algorithm",
            "http://www.w3.org/TR/2001/REC-xml-c14n20010315"
        )

        NSMAP = {
            "s": "http://schemas.xmlsoap.org/soap/envelope/"
        }

        envelope = etree.Element(
            etree.QName(NSMAP["s"], "Envelope"),
            nsmap=NSMAP
        )

        header = etree.SubElement(envelope, etree.QName(NSMAP["s"], "Header"))

        activity_id = str(uuid.uuid4())

        activity = etree.SubElement(
            header,
            "ActivityId",
            nsmap={None: "http://schemas.microsoft.com/2004/09/ServiceModel/Diagnostics"},
            CorrelationId=activity_id
        )
        activity.text = activity_id

       

        body = etree.SubElement(
            envelope,
            etree.QName(NSMAP["s"], "Body"),
            nsmap={
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsd": "http://www.w3.org/2001/XMLSchema"
            }
        )

        NS_SAT = "http://DescargaMasivaTerceros.sat.gob.mx"

        solicita_descarga = etree.SubElement(
            body,
            "SolicitaDescargaRecibidos",
            nsmap={None: NS_SAT}
        )

        solicita_descarga.append(solicitud)

        xml_request = etree.tostring(
            envelope,
            encoding="utf-8",
            xml_declaration=True
        )
        token = token.replace("\n", "").replace("\r", "").strip()
        headers = {
            "Content-Type": "application/soap+xml; charset=utf-8",
            "Authorization": f'WRAP access_token="{token}"'
        }

        _logger.error("===== XML QUE ESTÁS GENERANDO =====")
        _logger.error(xml_request.decode())
        
        response = requests.post(
            "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc",
            data=xml_request,
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "Authorization": f'WRAP access_token="{token}"',
                "SOAPAction": '"http://DescargaMasivaTerceros.sat.gob.mx/ISolicitaDescargaService/SolicitaDescargaRecibidos"'
            }
        )

        #response = requests.post(url, data=xml_request, headers=headers)


        _logger.error("===== HEADERS ENVIADOS =====")
        _logger.error(response.request.headers)

        _logger.error("===== BODY ENVIADO =====")
        _logger.error(response.request.body.decode() if isinstance(response.request.body, bytes) else response.request.body)
        

            
        data = response
        if response.status_code != 200:
            raise UserError(f"Error SAT {response.status_code}: {response.text}")
        else:
            _logger.error(response.status_code)
            _logger.error(response.text)
            _logger.error(response)
            root = etree.fromstring(response.text)
            ns = {
                "s": "http://schemas.xmlsoap.org/soap/envelope/",
                "sat": "http://DescargaMasivaTerceros.sat.gob.mx"
            }

            result = root.xpath(
                "//sat:SolicitaDescargaRecibidosResult",
                namespaces=ns
            )

            if result:
                node = result[0]

                id_solicitud = node.get("IdSolicitud")
                rfc_solicitante = node.get("RfcSolicitante")
                cod_estatus = node.get("CodEstatus")
                mensaje = node.get("Mensaje")

                return {
                    "id_solicitud":id_solicitud,
                    "rfc_solicitante":rfc_solicitante,
                    "cod_estatus":cod_estatus,
                    "mensaje": mensaje
                }

    def request_status(self, certificate, request_id, requester_vat):
        data = ""
        url = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc"

        auth_result = self._auth(certificate)

        if not auth_result["success"]:
            raise UserError("No fue posible autenticarse con el SAT")

        token = auth_result["token"]


        NS_SAT = "http://DescargaMasivaTerceros.sat.gob.mx"
        solicitud = etree.Element(
            etree.QName(NS_SAT, "solicitud"),
            IdSolicitud=request_id,
            RfcSolicitante=requester_vat
        )

        signature_node = xmlsec.template.create(
            solicitud,
            xmlsec.Transform.C14N,      
            xmlsec.Transform.RSA_SHA1
        )
        solicitud.insert(0, signature_node)

        ref = xmlsec.template.add_reference(
            signature_node,
            xmlsec.Transform.SHA1,
            uri=""
        )

        cer_bytes = base64.b64decode(certificate.content)

        cert = x509.load_der_x509_certificate(cer_bytes, default_backend())

        issuer_name = cert.issuer.rfc4514_string()
        serial_number = str(cert.serial_number)


        xmlsec.template.add_transform(ref, xmlsec.Transform.ENVELOPED)

        key_info = xmlsec.template.ensure_key_info(signature_node)
        x509_data = xmlsec.template.add_x509_data(key_info)

        issuer_serial = xmlsec.template.x509_data_add_issuer_serial(x509_data)

        issuer_name_node = xmlsec.template.x509_issuer_serial_add_issuer_name(issuer_serial)
        issuer_name_node.text = issuer_name

        serial_node = xmlsec.template.x509_issuer_serial_add_serial_number(issuer_serial)
        serial_node.text = serial_number

        xmlsec.template.x509_data_add_certificate(x509_data)

        xmlsec.tree.add_ids(solicitud, ["Id"])

        cer_path, key_path = self._prepare_key_and_cert(certificate)

        key = xmlsec.Key.from_file(key_path, xmlsec.KeyFormat.PEM)
        key.load_cert_from_file(cer_path, xmlsec.KeyFormat.PEM)

        ctx = xmlsec.SignatureContext()
        ctx.key = key

        ctx.sign(signature_node)

        c14n_method = signature_node.find(
            ".//{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod"
        )
        c14n_method.set(
            "Algorithm",
            "http://www.w3.org/TR/2001/REC-xml-c14n20010315"
        )

        NSMAP = {
            "s": "http://schemas.xmlsoap.org/soap/envelope/",
            "des": "http://DescargaMasivaTerceros.sat.gob.mx"
        }

        envelope = etree.Element(
            etree.QName(NSMAP["s"], "Envelope"),
            nsmap=NSMAP
        )

        header = etree.SubElement(envelope, etree.QName(NSMAP["s"], "Header"))

        #activity_id = str(uuid.uuid4())

        #activity = etree.SubElement(
        #    header,
        #    "ActivityId",
        #    nsmap={None: "http://schemas.microsoft.com/2004/09/ServiceModel/Diagnostics"},
        #    CorrelationId=activity_id
        #)
        #activity.text = activity_id

       

        body = etree.SubElement(
            envelope,
            etree.QName(NSMAP["s"], "Body"),
            #nsmap={
            #    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            #    "xsd": "http://www.w3.org/2001/XMLSchema"
            #}
        )

        NS_SAT = "http://DescargaMasivaTerceros.sat.gob.mx"

        solicita_descarga = etree.SubElement(
            body,
            etree.QName(NS_SAT, "VerificaSolicitudDescarga")
        )

        solicita_descarga.append(solicitud)

        xml_request = etree.tostring(
            envelope,
            encoding="utf-8",
            xml_declaration=True
        )
        token = token.replace("\n", "").replace("\r", "").strip()
        headers = {
            "Content-Type": "application/soap+xml; charset=utf-8",
            "Authorization": f'WRAP access_token="{token}"'
        }

        _logger.error("===== XML QUE ESTÁS GENERANDO =====")
        _logger.error(xml_request.decode())
        
        
        response = requests.post(
            "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc",
            data=xml_request,
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "Authorization": f'WRAP access_token="{token}"',
                "SOAPAction": '"http://DescargaMasivaTerceros.sat.gob.mx/IVerificaSolicitudDescargaService/VerificaSolicitudDescarga"'
            }
        )

        if response.status_code != 200:
            raise UserError(f"Error SAT {response.status_code}: {response.text}")
        else:
            _logger.error(response.status_code)
            _logger.error(response.text)
            _logger.error(response)

            ns = {
                "s": "http://schemas.xmlsoap.org/soap/envelope/",
                "sat": "http://DescargaMasivaTerceros.sat.gob.mx"
            }

            root = etree.fromstring(response.text)

            node = root.xpath(
                "//sat:VerificaSolicitudDescargaResult",
                namespaces=ns
            )[0]

            if node:

                estado_solicitud = node.get("EstadoSolicitud")
                cod_estatus_solicitud = node.get("CodigoEstadoSolicitud")
                codigo_estatus = node.get("CodEstatus")
                mensaje = node.get("Mensaje")
                numero_cfdi = node.get("NumeroCFDIs")

                paquetes = node.xpath(
                    ".//sat:IdsPaquetes/text()",
                    namespaces=ns
                )
                
                return {
                    "estado_solicitud":estado_solicitud,
                    "cod_estatus_solicitud":cod_estatus_solicitud,
                    "codigo_estatus":codigo_estatus,
                    "mensaje": mensaje,
                    "numero_cfdi": numero_cfdi,
                    "paquetes": paquetes
                }

    def download_package(self, certificate, package_id, requester_vat):
     
        auth_result = self._auth(certificate)

        if not auth_result["success"]:
            raise UserError("No fue posible autenticarse con el SAT")

        token = auth_result["token"]


        NS_SAT = "http://DescargaMasivaTerceros.sat.gob.mx"
        solicitud = etree.Element(
            etree.QName(NS_SAT, "peticionDescarga"),
            IdPaquete=package_id,
            RfcSolicitante=requester_vat
        )

        signature_node = xmlsec.template.create(
            solicitud,
            xmlsec.Transform.C14N,      
            xmlsec.Transform.RSA_SHA1
        )
        solicitud.insert(0, signature_node)

        ref = xmlsec.template.add_reference(
            signature_node,
            xmlsec.Transform.SHA1,
            uri=""
        )

        cer_bytes = base64.b64decode(certificate.content)

        cert = x509.load_der_x509_certificate(cer_bytes, default_backend())

        issuer_name = cert.issuer.rfc4514_string()
        serial_number = str(cert.serial_number)


        xmlsec.template.add_transform(ref, xmlsec.Transform.ENVELOPED)

        key_info = xmlsec.template.ensure_key_info(signature_node)
        x509_data = xmlsec.template.add_x509_data(key_info)

        issuer_serial = xmlsec.template.x509_data_add_issuer_serial(x509_data)

        issuer_name_node = xmlsec.template.x509_issuer_serial_add_issuer_name(issuer_serial)
        issuer_name_node.text = issuer_name

        serial_node = xmlsec.template.x509_issuer_serial_add_serial_number(issuer_serial)
        serial_node.text = serial_number

        xmlsec.template.x509_data_add_certificate(x509_data)

        xmlsec.tree.add_ids(solicitud, ["Id"])

        cer_path, key_path = self._prepare_key_and_cert(certificate)

        key = xmlsec.Key.from_file(key_path, xmlsec.KeyFormat.PEM)
        key.load_cert_from_file(cer_path, xmlsec.KeyFormat.PEM)

        ctx = xmlsec.SignatureContext()
        ctx.key = key

        ctx.sign(signature_node)

        c14n_method = signature_node.find(
            ".//{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod"
        )
        c14n_method.set(
            "Algorithm",
            "http://www.w3.org/TR/2001/REC-xml-c14n20010315"
        )

        NSMAP = {
            "s": "http://schemas.xmlsoap.org/soap/envelope/",
            "des": "http://DescargaMasivaTerceros.sat.gob.mx"
        }

        envelope = etree.Element(
            etree.QName(NSMAP["s"], "Envelope"),
            nsmap=NSMAP
        )

        header = etree.SubElement(envelope, etree.QName(NSMAP["s"], "Header"))

        body = etree.SubElement(
            envelope,
            etree.QName(NSMAP["s"], "Body"),
        )

        NS_SAT = "http://DescargaMasivaTerceros.sat.gob.mx"

        solicita_descarga = etree.SubElement(
            body,
            etree.QName(NS_SAT, "PeticionDescargaMasivaTercerosEntrada")
        )

        solicita_descarga.append(solicitud)

        xml_request = etree.tostring(
            envelope,
            encoding="utf-8",
            xml_declaration=True
        )
        token = token.replace("\n", "").replace("\r", "").strip()
        

        _logger.error("===== XML QUE ESTÁS GENERANDO =====")
        _logger.error(xml_request.decode())
        
        

        response = requests.post(
            "https://cfdidescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc",
            data=xml_request,
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "Authorization": f'WRAP access_token="{token}"',
                "SOAPAction": '"http://DescargaMasivaTerceros.sat.gob.mx/IDescargaMasivaTercerosService/Descargar"'
            }
        )

        if response.status_code != 200:
            raise UserError(f"Error SAT {response.status_code}: {response.text}")
        else:
            _logger.error(response.status_code)
            _logger.error(response.text)
            _logger.error(response)
            root = etree.fromstring(response.text)  # response debe ser bytes o string

            ns = {
                's': 'http://schemas.xmlsoap.org/soap/envelope/',
                'sat': 'http://DescargaMasivaTerceros.sat.gob.mx'
            }

            paquete = root.xpath(
                './/sat:Paquete/text()',
                namespaces=ns
            )
            if paquete:
                _logger.error(paquete)
                paquete_b64 = paquete[0]
                return paquete_b64
           
  