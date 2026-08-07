from odoo.addons.survey.controllers.main import Survey
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class SurveyAuditController(Survey):
    
    def survey_start(self, survey_token, answer_token=None, email=False, **post):
        """Captura el idx y actualiza el user_input existente"""
        responder_idx = post.get('idx') or request.params.get('idx')
        
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
        
        if access_data.get('answer_sudo'):
            user_input = access_data['answer_sudo']
            
            if responder_idx is not None and user_input.state in ['new', 'in_progress']:
                user_input.set_responder(int(responder_idx))
        
        return super().survey_start(survey_token, answer_token=answer_token, email=email, **post)