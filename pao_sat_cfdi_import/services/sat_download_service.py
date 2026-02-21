import base64
import uuid
from datetime import datetime, timedelta
from lxml import etree
from zeep import Client
from OpenSSL import crypto

class SATDownloadService:
    AUTH_WSDL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion.svc?wsdl"
    REQUEST_WSDL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc?wsdl"
    CONSULT_WSDL = "https://cfdidescargamasivaconsulta.clouda.sat.gob.mx/ConsultaSolicitudService.svc?wsdl"
    DOWNLOAD_WSDL = "https://cfdidescargamasivaconsulta.clouda.sat.gob.mx/DescargaService.svc?wsdl"

    def __init__(self, rfc, cer_path, key_path, key_password):
        self.rfc = rfc
        self.cer_path = cer_path
        self.key_path = key_path
        self.key_password = key_password
        self.token = None
    
    def auth(self):
        client = Client(self.AUTH_WSDL)

        signed_xml = self._generate_xml_auth()

        response = client.service.Autentica(signed_xml)

        self.token = response
        return self.token
    
    def _generate_xml_auth(self):
        
        created = datetime.utcnow()
        expires = created + timedelta(minutes=5)

       
        root = etree.Element("Autenticacion")
        etree.SubElement(root, "Created").text = created.strftime('%Y-%m-%dT%H:%M:%S')
        etree.SubElement(root, "Expires").text = expires.strftime('%Y-%m-%dT%H:%M:%S')

        return etree.tostring(root)
    
    def request_download(self, start_date, end_date, document_type):
        if not self.token:
            raise Exception("Debe autenticarse primero")

        client = Client(self.REQUEST_WSDL)

        response = client.service.SolicitaDescarga(
            RfcEmisor=None,
            RfcReceptor=self.rfc,
            FechaInicial=fecha_inicio,
            FechaFinal=end_date,
            TipoSolicitud="CFDI",
            TipoComprobante=document_type,
            EstadoComprobante="Vigente"
        )

        return response.IdSolicitud
    
    def get_state(self, request_id):
        client = Client(self.CONSULT_WSDL)

        response = client.service.ConsultaSolicitud(
            RfcSolicitante=self.rfc,
            IdSolicitud=request_id
        )
        return response
    
    def download_package(self, package_id):
        client = Client(self.DOWNLOAD_WSDL)

        response = client.service.Descarga(
            RfcSolicitante=self.rfc,
            IdPaquete=package_id
        )

        return base64.b64decode(response.Paquete)