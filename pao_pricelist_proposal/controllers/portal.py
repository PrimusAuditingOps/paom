from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from werkzeug.urls import url_join
import base64

class ProposalPortal(portal.CustomerPortal):

    @http.route('/pricelist_proposal/<int:id>/<string:token>', type='http', auth='public', website=True)
    def proposal_portal(self, id, token):
        try:
            proposal_sudo = self._document_check_access('pao.pricelist.proposal', id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        base_pricelist = proposal_sudo.get_current_base_pricelist()
        # lang_code = proposal_sudo.customer_id.lang if proposal_sudo.customer_id else 'en_US'
        # request.env.context = dict(request.env.context, lang=lang_code)
        
        if proposal_sudo and proposal_sudo.proposal_status == 'sent':
            accept_link = '/pricelist_proposal/%s/%s/accept' % (id, token)
            reject_link = '/pricelist_proposal/%s/%s/confirm_reject' % (id, token)
            return request.render('pao_pricelist_proposal.pricelist_portal_template', 
                                  {'proposal': proposal_sudo, 'accept_link': accept_link, 'confirm_reject_link': reject_link, 'base_pricelist': base_pricelist})
        elif proposal_sudo and proposal_sudo.proposal_status in ('reject', 'accept'):
            attachment = proposal_sudo.proposal_agreement_id
            return request.render('pao_pricelist_proposal.pricelist_proposal_response_sent', 
                                  {'attachment': attachment})
        else:
            return request.render('pao_pricelist_proposal.pricelist_proposal_exception_page_view')
        
    
    @http.route(['/pricelist_proposal/<int:id>/<string:token>/accept'], type='json', auth="public", website=True)
    def proposal_portal_accept(self, id, token, signature):
        if not signature:
            redirect_link = '/pricelist_proposal/%s/%s' % (id, token)
            return request.redirect(redirect_link)
        
        try:
            proposal_sudo = self._document_check_access('pao.pricelist.proposal', id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        proposal_sudo.signature = signature
        accept_proposal = proposal_sudo.accept_proposal_action()
        
        if accept_proposal:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            redirect_link = url_join(base_url, '/pricelist_proposal/%s/%s' % (id, token))
            return {
                'force_refresh': True,
                'redirect_url':  redirect_link
            }
        
    @http.route(['/pricelist_proposal/<int:id>/<string:token>/confirm_reject'], type='http', auth="public", website=True, methods=['POST','GET'])
    def proposal_portal_confirm_reject(self, id, token, **kwargs):
        if request.httprequest.method != 'POST':
            redirect_link = '/pricelist_proposal/%s/%s' % (id, token)
            return request.redirect(redirect_link)

        try:
            proposal_sudo = self._document_check_access('pao.pricelist.proposal', id, access_token=token)
        except (AccessError, MissingError):
            return request.render('pao_pricelist_proposal.pricelist_proposal_exception_page_view')
        
        reasons = kwargs.get('reject_reasons')
        proposal_sudo.set_reject_reasons(reasons)
        reject_proposal = proposal_sudo.reject_proposal_action()
        
        # request.env.context = dict(request.env.context, lang=proposal_sudo.customer_id.lang)
        
        if reject_proposal:
            return request.render('pao_pricelist_proposal.pricelist_proposal_response_sent')
        else:
            return request.render('pao_pricelist_proposal.pricelist_proposal_response_error')
    
    @http.route(['/download_attachment/<int:attachment_id>'], type='http', auth="public", website=True)
    def download_attachment(self, attachment_id, **kw):
        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
        if attachment and attachment.datas and attachment.mimetype == 'application/pdf':
            pdf_data = base64.b64decode(attachment.datas)
            file_name = _("Proposal Agreement") + ".pdf"
            response = http.request.make_response(
                pdf_data,
                [('Content-Type', 'application/pdf'), ('Content-Disposition', 'attachment; filename=%s' % file_name)]
            )
            return response
        else:
            return http.request.not_found()
        

    