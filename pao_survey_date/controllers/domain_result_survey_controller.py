from odoo.addons.survey.controllers.main import Survey as SurveyController
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from logging import getLogger
from odoo import fields, http, _
from odoo.http import request
_logger = getLogger(__name__)
from datetime import datetime, timedelta

class DomainResultSurveyController(SurveyController):

    def _get_results_page_user_input_domain(self, survey, **post):
        # Llamamos al método original
        domain = super()._get_results_page_user_input_domain(survey, **post)

        # Agregamos o modificamos la lógica
        if post.get('pao_date') and post.get('pao_end_date'):

            date = post.get('pao_date') 
            to_date = post.get('pao_end_date') 
            start_date = datetime.strptime(date, '%Y-%m-%d')
            end_date = datetime.strptime(to_date, '%Y-%m-%d')
            next_day = end_date + timedelta(days=1)
            domain = expression.AND([[('create_date', '>=', selected_date),('create_date', '<', next_day)], domain])

        return domain
    
    