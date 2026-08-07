# -*- coding: utf-8 -*-
from odoo.addons.survey.controllers.main import Survey
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class SurveyAuditController(Survey):
    
    def survey_start(self, survey_token, answer_token=None, email=False, **post):
        """
        Extiende survey_start para capturar el email del respondent.
        """
        # Captura respondent_email de los parámetros POST/GET
        respondent_email = post.get('respondent_email')
        if respondent_email:
            request.session['survey_respondent_email'] = respondent_email
            _logger.info("Survey respondent email captured: %s", respondent_email)
        
        # Llama al método original con todos sus parámetros
        return super().survey_start(survey_token, answer_token=answer_token, email=email, **post)