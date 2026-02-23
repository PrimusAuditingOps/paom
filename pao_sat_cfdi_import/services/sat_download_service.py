import base64
import uuid
import pytz
from datetime import datetime, timedelta
from lxml import etree
from zeep import Client
from cryptography.hazmat.primitives.serialization import load_der_private_key
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509


class SATDownloadService(models.AbstractModel):
    _name = "pao.sat.service":
    #AUTH_WSDL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion.svc?wsdl"
    #REQUEST_WSDL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc?wsdl"
    #CONSULT_WSDL = "https://cfdidescargamasivaconsulta.clouda.sat.gob.mx/ConsultaSolicitudService.svc?wsdl"
    #DOWNLOAD_WSDL = "https://cfdidescargamasivaconsulta.clouda.sat.gob.mx/DescargaService.svc?wsdl"

    AUTH_WSDL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion.svc?wsdl"


    def auth_sat(rfc, cer_bytes, key_bytes, key_password):

        cer_bytes = base64.b64decode(cer_bytes)
        key_bytes = base64.b64decode(key_bytes)

        cert = x509.load_der_x509_certificate(cer_bytes)
        cert_b64 = base64.b64encode(cer_bytes).decode()

        private_key = load_der_private_key(
            key_bytes,
            password=key_password.encode()
        )

        requested_tz = pytz.timezone('America/Mexico_City')
        created = requested_tz.fromutc(datetime.utcnow())
        created = created.date()
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