
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from logging import getLogger
from werkzeug.urls import url_join
import base64
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = getLogger(__name__)

class CustomerPortal(portal.CustomerPortal):

    
    @http.route(['/sign/sa/<int:sa_id>/<string:sa_token>/accept'], type='json', auth="public", website=True)
    def portal_sa_accept(self, sa_id, sa_token, name=None, signature=None):
        try:
            sa_sudo = self._document_check_access('pao.sign.sa.agreements.sent', sa_id, access_token=sa_token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        lang = sa_sudo.signer_id.lang or sa_sudo.create_uid.lang
        sa_sudo.with_context(lang=lang)
        zone = sa_sudo.create_uid.tz
        requested_tz = pytz.timezone(zone)
        today = requested_tz.fromutc(datetime.utcnow())

        signature_date = today
        sa_sudo.write({"signature": signature, "signer_name": name, "signature_date": signature_date})

        
        attachment_list = []
        for rn_sa in sa_sudo.registration_number_to_sign_ids:
            

            filename = "%s-%s.%s" % (rn_sa.name,rn_sa.organization_name, "pdf")
            pdf = request.env.ref('pao_sign_sa.report_service_agreements').sudo()._render_qweb_pdf([sa_id], data= {"values": rn_sa, "print": True})[0]
            attachment = request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'datas': base64.b64encode(pdf),
                    'res_model': 'pao.sign.sa.agreements.sent',
                    'res_id': sa_id,
                    'type': 'binary',  # override default_type from context, possibly meant for another model!
                })
            attachment_list.append(attachment.id)
        
        #_logger.error(request.httprequest.remote_addr) 
        #_logger.error(request.session['geoip'].get('latitude') or 0.0)
        #_logger.error(request.session['geoip'].get('longitude') or 0.0)
        sa_sudo.write({"attachment_ids": [(6, 0, attachment_list)], "document_status": "sign"})
        msg = "Se ha firmado el acuerdo " + sa_sudo.title
        notification_ids = []
        notification_ids.append((0,0,{
            'res_partner_id':sa_sudo.create_uid.id,
            'notification_type':'inbox'
        }))
        sa_sudo.sale_order_id.message_post(body=msg)
    
        #.message_post(body=msg, partner_ids=[sa_sudo.create_uid.id]) 
        #sa_sudo.write({'signature_name': name, 'signature': signature, 'document_status': 'sign'})
        #signature_date 


        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'force_refresh': True,
            'redirect_url':  url_join(base_url, '/sign/sa/%s/%s' % (sa_id, sa_token))
        }

    @http.route(['/sign/sa/<int:sa_id>/<string:sa_token>'], type='http', auth="public", website=True)
    def portal_sign_sa(self, report_type=None, sa_id=False, sa_token=None, download=False, **kw):
        
        try:
            sa_sudo = self._document_check_access('pao.sign.sa.agreements.sent', sa_id, access_token=sa_token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        documents = []
        url = ""
 
        lang = sa_sudo.signer_id.lang or sa_sudo.create_uid.lang
        
        if sa_sudo.document_status == "sent":
            url = '/sign/sa/'+str(sa_id)+'/'+sa_token+'/accept'
        elif sa_sudo.document_status == "sign":
            url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') 
            for attach in sa_sudo.attachment_ids:
                if not attach.access_token:
                        token = attach._generate_access_token()
                        attach.write({"access_token": token})
                
                
                documents.append({"name": attach.name, "url": url+"/web/content/"+str(attach.id)+"?download=true&access_token="+str(attach.access_token)})
        else:
            return request.render('pao_sign_sa.pao_sign_sa_exception_page_view', {})

        
        return request.render('pao_sign_sa.sa_portal_template', {"serviceagreement": sa_sudo, "print": False, "urlAccept": url, "documents": documents })