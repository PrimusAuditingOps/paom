from odoo.addons.survey.controllers.main import Survey
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class SurveyAuditController(Survey):
    
    def survey_start(self, survey_token, answer_token=None, email=False, **post):
        """Captura el idx y actualiza el user_input existente"""
        responder_idx = post.get('idx') or request.params.get('idx')
        
        _logger.warning("survey_start called with survey_token: %s, answer_token: %s, email: %s, idx: %s", survey_token, answer_token, email, responder_idx)
        
        # Obtén el user_input antes de proceder
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
        
        if access_data.get('user_input_id'):
            user_input = request.env['survey.user_input'].browse(access_data['user_input_id'])
            
            # Actualiza el respondent_idx si viene en la URL
            if responder_idx is not None:
                user_input.write({
                    'respondent_idx': int(responder_idx),
                })
                _logger.info("Updated user_input %s with respondent_idx: %s", user_input.id, responder_idx)
        
        return super().survey_start(survey_token, answer_token=answer_token, email=email, **post)