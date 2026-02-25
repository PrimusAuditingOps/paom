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
from lxml import etree
from zeep import Client
from zeep.transports import Transport
from requests import Session
import xmlsec
import tempfile
import subprocess
from OpenSSL import crypto
from logging import getLogger
from datetime import datetime, timedelta, timezone
from odoo import models
from odoo.exceptions import UserError


_logger = getLogger(__name__)

class SATDownloadService(models.AbstractModel):
    _name = "pao.sat.service"
    #AUTH_WSDL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion.svc?wsdl"
    #REQUEST_WSDL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc?wsdl"
    #CONSULT_WSDL = "https://cfdidescargamasivaconsulta.clouda.sat.gob.mx/ConsultaSolicitudService.svc?wsdl"
    #DOWNLOAD_WSDL = "https://cfdidescargamasivaconsulta.clouda.sat.gob.mx/DescargaService.svc?wsdl"

    #AUTH_WSDL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion.svc?wsdl"
    #AUTH_WSDL = "https://cfdidescargamasiva.sat.gob.mx/Autenticacion.svc?wsdl"
    AUTH_WSDL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc?wsdl"



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

    # -----------------------------------------------------------------
    # Ccambios
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # Firmar usando certificado almacenado en Odoo
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # Método públicor aqui
    # -----------------------------------------------------------------
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
        auth_result = self._auth(certificate)
        fecha_inicio_dt = datetime.combine(start_date, datetime.min.time())
        fecha_fin_dt = datetime.combine(end_date, datetime.max.time().replace(microsecond=0))

        fecha_inicio_str = fecha_inicio_dt.strftime('%Y-%m-%dT%H:%M:%S')
        fecha_fin_str = fecha_fin_dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        if auth_result["success"]:
            token = auth_result["token"]


            NSMAP = {
                's': 'http://schemas.xmlsoap.org/soap/envelope/',
                'des': 'http://DescargaMasivaTerceros.sat.gob.mx'
            }

            envelope = etree.Element(
                '{http://schemas.xmlsoap.org/soap/envelope/}Envelope',
                nsmap=NSMAP
            )

            body = etree.SubElement(
                envelope,
                '{http://schemas.xmlsoap.org/soap/envelope/}Body'
            )

            solicita = etree.SubElement(
                body,
                '{http://DescargaMasivaTerceros.sat.gob.mx}SolicitaDescarga'
            )

            solicitud = etree.SubElement(
                solicita,
                '{http://DescargaMasivaTerceros.sat.gob.mx}solicitud'
            )

            etree.SubElement(
                solicitud,
                '{http://DescargaMasivaTerceros.sat.gob.mx}RfcSolicitante'
            ).text = certificate.vat

            etree.SubElement(
                solicitud,
                '{http://DescargaMasivaTerceros.sat.gob.mx}FechaInicial'
            ).text = fecha_inicio_str

            etree.SubElement(
                solicitud,
                '{http://DescargaMasivaTerceros.sat.gob.mx}FechaFinal'
            ).text = fecha_fin_str

            etree.SubElement(
                solicitud,
                '{http://DescargaMasivaTerceros.sat.gob.mx}TipoSolicitud'
            ).text = "CFDI"


            xml_bytes = etree.tostring(envelope, encoding="utf-8", xml_declaration=True)

            response = requests.post(
                "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc",
                data=xml_bytes,
                headers = {
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": "http://DescargaMasivaTerceros.sat.gob.mx/ISolicitaDescargaService/SolicitaDescarga",
                    "Authorization": f'WRAP access_token="{token}"'
                }
            )
            _logger.error(response)
            _logger.error(response.status_code)
            _logger.error(response.text)
            data = response
        
        return data

    https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc
    https://cfdidescargamasiva.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc
    https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc