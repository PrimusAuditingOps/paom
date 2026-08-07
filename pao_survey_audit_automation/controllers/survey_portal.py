from odoo.addons.survey.controllers.main import SurveyController
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class SurveyAuditController(SurveyController):
    
    def _prepare_survey_user_input_context(self, survey, **kwargs):
        """Captura respondent_email antes de crear el user_input"""
        # Captura el email si viene en los parámetros de la URL
        respondent_email = request.params.get('respondent_email')
        if respondent_email:
            request.session['survey_respondent_email'] = respondent_email
            _logger.info("Survey respondent email captured: %s", respondent_email)
        
        # Llama al método original
        return super()._prepare_survey_user_input_context(survey, **kwargs)