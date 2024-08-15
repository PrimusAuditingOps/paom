from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from werkzeug.urls import url_join
import base64

class ReminderPortal(portal.CustomerPortal):
    
    @http.route(['/anniversary_reminder/<int:id>/<string:token>'], type='http', auth="public", website=True)
    def reminder_portal_action_selection(self, id, token, **kwargs):
        try:
            reminder_sudo = self._document_check_access('pao.anniversary.reminder', id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        if reminder_sudo.status in ('pending', 'progress', 'confirm', 'lost'):
            return request.render('pao_anniversary_reminder.reminder_exception_page_view')
        
        action = request.params.get('action')
        action_label = _('Accept') if action == 'accept' else _('Reject')
        action_link = '/anniversary_reminder/%s/%s/response' % (id, token)
        
        return request.render('pao_anniversary_reminder.reminder_response_template', 
                                {'action_label': action_label, 'action': action, 'action_link': action_link})
    
    @http.route(['/anniversary_reminder/<int:id>/<string:token>/response'], type='http', auth="public", website=True, methods=['POST','GET'])
    def reminder_portal_response(self, id, token, **kwargs):
        if request.httprequest.method != 'POST':
            redirect_link = '/anniversary_reminder/%s/%s' % (id, token)
            return request.redirect(redirect_link)
        
        try:
            reminder_sudo = self._document_check_access('pao.anniversary.reminder', id, access_token=token)
        except (AccessError, MissingError):
            return request.render('pao_anniversary_reminder.reminder_exception_page_view')
        
        action = kwargs.get('action')
        observations = kwargs.get('observations')
        
        if action == 'accept':
            reminder_sudo.accept_audit(observations)
        else:
            reminder_sudo.decline_audit(observations)
        
        return request.render('pao_anniversary_reminder.response_sent_template')

        

    