from odoo import http, _
from odoo.http import request
import logging
import io
import zipfile
import base64
from odoo.addons.web.controllers.main import content_disposition

_logger = logging.getLogger(__name__)
class ServiceAgreementsPortal(http.Controller):
    
    def user_has_sa(self):
        user = request.env.user.partner_id
        return bool(user.pao_agreements_ids)
    
    
    @http.route('/my/service_agreements', type='http', methods=['GET'], auth='user', website=True, sitemap=False)
    def my_service_agreements(self, **kwargs):
        
        if not self.user_has_sa():
            return request.redirect('/my/home')
        
        request.session.pop('error_sa_partner', None)
        
        partner_id = request.env.user.partner_id
        
        service_agreements = request.env['pao.sign.sa.agreements.sent'].sudo().search([
            ('signer_id', 'in', [partner_id.id] + partner_id.child_ids.ids),
            ('document_status', 'not in', ('cancel', 'exception'))
        ])
        
        return request.render('pao_client_sa_inquiry.my_service_agreements_view', {'service_agreements': service_agreements, 'page_name': 'partner_sa_list'})
    
    
    @http.route('/my_service_agreements/download/attachments/<int:id>', type='http', auth="user", website=True)
    def download_sa_attachments(self, id=None, **kwargs):
        # Buscar el registro correspondiente en el modelo pao.sign.sa.agreements.sent
        agreement = request.env['pao.sign.sa.agreements.sent'].sudo().browse(id)

        # Verificar que exista el registro
        if not agreement or not agreement.attachment_ids or agreement.signer_id.id != request.env.user.partner_id.id:
            return request.not_found()

        # Crear un buffer para el archivo zip
        zip_buffer = io.BytesIO()

        # Crear el archivo ZIP
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for attachment in agreement.attachment_ids:
                # Descargar el contenido del adjunto y decodificar el archivo en base64
                file_data = base64.b64decode(attachment.datas)
                file_name = attachment.name

                # Añadir el archivo al zip
                zip_file.writestr(file_name, file_data)

        # Preparar la respuesta
        zip_buffer.seek(0)
        zip_filename = 'Service_Agreements_Attachments_%s.zip' % agreement.title.replace(' ', '_')
        return request.make_response(
            zip_buffer.getvalue(),
            [
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', content_disposition(zip_filename))
            ]
        )