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
from datetime import datetime, timedelta
from odoo import models


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
        requested_tz = pytz.timezone('America/Mexico_City')
        created = requested_tz.fromutc(datetime.utcnow())
        expires = created + timedelta(minutes=5)

        return (
            created.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            expires.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        )

    # -----------------------------------------------------------------
    # Ccambios
    # -----------------------------------------------------------------
    def _build_envelope(self, cert_b64):

        created, expires = self._create_timestamp()
        token_id = f"uuid-{uuid.uuid4()}-1"

        NSMAP = {
            's': 'http://schemas.xmlsoap.org/soap/envelope/',
            'u': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd',
            'o': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
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
                '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Id': 'SECURITY-1'
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

        binary_token.text = cert_b64

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

        # Crear referencia
        ref = xmlsec.template.add_reference(
            signature_node,
            xmlsec.Transform.SHA1,
            uri='#SECURITY-1'   # <--- este cambio es crucial
        )

        xmlsec.template.add_transform(ref, xmlsec.Transform.EXCL_C14N)

        # Obtener PEM ya convertido correctamente
        cer_path, key_path = self._prepare_key_and_cert(certificate)

        
        # Cargar key PEM limpia
        key = xmlsec.Key.from_file(key_path, xmlsec.KeyFormat.PEM)
        key.load_cert_from_file(cer_path, xmlsec.KeyFormat.PEM)

        ctx = xmlsec.SignatureContext()
        ctx.key = key
        xmlsec.enable_debug_trace(True)
        # Firmar
        ctx.sign(signature_node)

        return envelope

    # -----------------------------------------------------------------
    # Método públicor aqui
    # -----------------------------------------------------------------
    def auth(self,certificate):

        cert_b64 = base64.b64encode(
            base64.b64decode(certificate.content)
        ).decode()

        envelope, token_id = self._build_envelope(cert_b64)
        signed_envelope = self._sign(envelope, certificate, token_id)
        _logger.error(etree.tostring(signed_envelope,pretty_print=True,encoding="unicode"))
        session = Session()
        transport = Transport(session=session)

        client = Client(self.AUTH_WSDL, transport=transport)

        response = client.transport.post(
            client.wsdl.location,
            etree.tostring(signed_envelope),
            headers={'Content-Type': 'text/xml; charset=utf-8'}
        )

        return response.content

    """
    def auth_sat(self, rfc, cer_base64, key_base64, password):
      
        cer_bytes = base64.b64decode(cer_base64)
        key_bytes = base64.b64decode(key_base64)

        cert = x509.load_der_x509_certificate(cer_bytes)
        cert_b64 = base64.b64encode(cer_bytes).decode()

        private_key = load_der_private_key(
            key_bytes,
            password=key_password.encode()
        )

        requested_tz = pytz.timezone('America/Mexico_City')
        created = requested_tz.fromutc(datetime.utcnow())
        #created = created.date()
        expires = created + timedelta(minutes=5)

        created_str = created.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        expires_str = expires.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

  
        NSMAP = {
            's': 'http://www.w3.org/2003/05/soap-envelope',
            'u': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd'
        }

        envelope = etree.Element(
            '{http://www.w3.org/2003/05/soap-envelope}Envelope',
            nsmap=NSMAP
        )

        header = etree.SubElement(
            envelope,
            '{http://www.w3.org/2003/05/soap-envelope}Header'
        )

        security = etree.SubElement(
            header,
            'Security',
            nsmap={'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd'}
        )

        timestamp = etree.SubElement(
            security,
            '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Timestamp'
        )

        etree.SubElement(timestamp, 'Created').text = created_str
        etree.SubElement(timestamp, 'Expires').text = expires_str

        timestamp_c14n = etree.tostring(timestamp, method="c14n")

        digest = hashes.Hash(hashes.SHA256())
        digest.update(timestamp_c14n)
        digest_value = base64.b64encode(digest.finalize()).decode()

        signature = private_key.sign(
            timestamp_c14n,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        signature_b64 = base64.b64encode(signature).decode()

        signature_node = etree.SubElement(security, 'Signature')

        signed_info = etree.SubElement(signature_node, 'SignedInfo')
        etree.SubElement(signed_info, 'DigestValue').text = digest_value

        etree.SubElement(signature_node, 'SignatureValue').text = signature_b64

        key_info = etree.SubElement(signature_node, 'KeyInfo')
        x509_data = etree.SubElement(key_info, 'X509Data')
        etree.SubElement(x509_data, 'X509Certificate').text = cert_b64

        xml_string = etree.tostring(envelope, encoding="utf-8")

        client = Client(self.AUTH_WSDL)

        response = client.service.Autentica(xml_string)

        return response

    """