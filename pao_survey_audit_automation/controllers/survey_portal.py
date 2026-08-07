# -*- coding: utf-8 -*-
from odoo.addons.survey.controllers.main import Survey
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class SurveyAudit(Survey):
    
    def survey_start(self, survey_id, **post):
        """Captura respondent_email antes de iniciar la encuesta"""
        # Captura el email si viene en los parámetros
        respondent_email = post.get('respondent_email')
        if respondent_email:
            request.session['survey_respondent_email'] = respondent_email
            _logger.info("Survey respondent email captured: %s", respondent_email)
        
        # Llama al método original
        return super().survey_start(survey_id, **post)