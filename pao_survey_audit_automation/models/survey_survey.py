import logging
from collections import Counter
from odoo import models, fields, api, http, _
from odoo.http import request
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo.addons.survey.controllers.main import Survey

_logger = logging.getLogger(__name__)

class SurveySurveyExtended(models.Model):
    _inherit = 'survey.survey'
    
    can_upload_file = fields.Boolean(default=False, copy=False)
    
    column_mapping_ids = fields.One2many(
        'survey.column.mapping',
        'survey_id',
        string='Column Mapping',
    )
    
    # Acción que abre el wizard de importación
    def action_open_import_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Audit File'),
            'res_model': 'survey.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_survey_id': self.id,
            },
        }

    # Envío de email a un contacto con el link único de la organización
    def _send_survey_mail_to_contact(self, email, partner_name, user_input, idx=None):
        """
        Envía un correo con el link de la encuesta al contacto indicado.
        Todos los contactos de una misma organización reciben el mismo token
        (mismo user_input), lo que garantiza una sola respuesta por organización.
        """
        self.ensure_one()
        if not email:
            return
        
        _logger.warning(email)
        _logger.warning(partner_name)

        survey_url = user_input.get_start_url()
        
        if idx:
            survey_url = survey_url+'&idx=%s' % idx

        try:
            template = self.env.ref('survey.mail_template_user_input_invite', raise_if_not_found=False)
            if template:
                template.with_context(
                    survey_url=survey_url,
                    partner_name=partner_name or email,
                    email_to=email,
                ).send_mail(
                    user_input.id,
                    force_send=True,
                    email_values={
                        'email_to': email,
                        'email_from': self.env.user.email_formatted,
                    },
                )
            else:
                # Envío básico si no existe la plantilla
                mail_vals = {
                    'subject': _('Survey: %s') % self.title,
                    'body_html': _(
                        '<p>Dear %s,</p>'
                        '<p>We invite you to complete the following survey:</p>'
                        '<p><a href="%s">%s</a></p>'
                        '<p>Thank you for your participation.</p>'
                    ) % (partner_name or email, survey_url, self.title),
                    'email_to': email,
                    'email_from': self.env.user.email_formatted,
                    'auto_delete': True,
                }
                self.env['mail.mail'].create(mail_vals).send()
        except Exception as exc:
            _logger.warning('Error sending survey to %s: %s', email, exc)

    # ── Método RPC para el dashboard OWL ──────────────────────────────────────
    @api.model
    def get_dashboard_data(self, date_from=None, date_to=None, survey_id=None):
        """
        Devuelve todos los datos necesarios para el dashboard en una sola llamada.
        Se filtra por la fecha de creación (envío) del user_input dentro del rango.
        """
        domain = [
            # ('imported_from_file', '=', True)
        ]

        if date_from:
            domain.append(('create_date', '>=', date_from + ' 00:00:00'))
        if date_to:
            domain.append(('create_date', '<=', date_to + ' 23:59:59'))
        if survey_id:
            domain.append(('survey_id', '=', survey_id))

        UserInput = self.env['survey.user_input']
        all_inputs = UserInput.search(domain)
        answered = all_inputs.filtered(lambda r: r.state == 'done')

        total_sent = len(all_inputs)
        total_answered = len(answered)

        max_score_indicator_available = False
        compliment_indicator_available = False
        complaint_indicator_available = False
        classification_available = False
        if answered:
            max_score_indicator_available = self.env['survey.question'].search([
                ('survey_id', 'in', answered.mapped('survey_id').ids),
                ('dashboard_feedback_type', '=', 'max_score_indicator'),
            ], limit=1)
            compliment_indicator_available = self.env['survey.question'].search([
                ('survey_id', 'in', answered.mapped('survey_id').ids),
                ('dashboard_feedback_type', '=', 'compliment'),
            ], limit=1)

            complaint_indicator_available = self.env['survey.question'].search([
                ('survey_id', 'in', answered.mapped('survey_id').ids),
                ('dashboard_feedback_type', '=', 'complaint'),
            ], limit=1)
            
            classification_available = (compliment_indicator_available or complaint_indicator_available)

        # ── Gráfica 2: encuestas con compliments ───────────
        with_compliments = len(answered.filtered('has_compliment_answer')) if compliment_indicator_available else None
        
        with_complaints = len(answered.filtered('has_complaint_answer')) if complaint_indicator_available else None

        # ── Gráfica 4: encuestados con calificación máxima en pregunta indicada ──────
        max_score = self._count_max_score(answered) if max_score_indicator_available else None

        # ── Gráfica 5: positivos / neutros / negativos ─────────────────────────
        if classification_available:
            positive, neutral, negative = self._classify_results(answered)
        else:
            positive = neutral = negative = None

        top_compliment_tags = self._top_tags(answered, 'compliment_theme_ids', limit=5)
        top_complaint_tags = self._top_tags(answered, 'complaint_theme_ids', limit=5)

        top_auditors_compliments = self._top_person_by_tag(
            answered, 'auditor_name', 'compliment_theme_ids', limit=5
        )
        top_auditors_complaints = self._top_person_by_tag(
            answered, 'auditor_name', 'complaint_theme_ids', limit=5
        )
        top_coordinators_compliments = self._top_person_by_tag(
            answered, 'coordinator_name', 'compliment_theme_ids', limit=5
        )
        top_coordinators_complaints = self._top_person_by_tag(
            answered, 'coordinator_name', 'complaint_theme_ids', limit=5
        )
        
        surveys = self.env['survey.survey'].search_read(
            [('id', 'in', all_inputs.mapped('survey_id').ids)],
            ['id', 'title'],
            order='title asc',
        )
        
        # surveys = self.env['survey.survey'].search_read(
        #     [('user_input_ids.imported_from_file', '=', True)],
        #     ['id', 'title'],
        #     order='title asc',
        # )

        return {
            'surveys': surveys,
            'total_sent': total_sent,
            'total_answered': total_answered,
            'has_compliment_indicator': bool(compliment_indicator_available),
            'has_complaint_indicator': bool(complaint_indicator_available),
            'with_compliments': with_compliments,
            'with_complaints': with_complaints,
            'has_max_score_indicator': bool(max_score_indicator_available),
            'max_score': max_score,
            'classification_available': bool(classification_available),
            'positive': positive,
            'neutral': neutral,
            'negative': negative,
            'top_compliment_tags': top_compliment_tags,
            'top_complaint_tags': top_complaint_tags,
            'top_auditors_compliments': top_auditors_compliments,
            'top_auditors_complaints': top_auditors_complaints,
            'top_coordinators_compliments': top_coordinators_compliments,
            'top_coordinators_complaints': top_coordinators_complaints,
        }

    # ── Helpers privados para el dashboard ────────────────────────────────────
    
    # def _get_answer_value(self, user_input, question_seq):
    #     """
    #     Devuelve el valor de respuesta (suggested_answer value_char o similar)
    #     para la pregunta con sequence = question_seq.
    #     Retorna None si no hay respuesta.
    #     """
    #     line = user_input.user_input_line_ids.filtered(
    #         lambda l: l.question_id.sequence == question_seq
    #     )
    #     _logger.warning(
    #         'user_input_id=%s | question_id=%s | sequence=%s | question=%s',
    #         user_input.id,
    #         line.question_id.id,
    #         line.question_id.sequence,
    #         line.question_id.title
    #     )
    #     _logger.warning('Buscando respuesta para pregunta_seq=%s en user_input_id=%s: line=%s', question_seq, user_input.id, line)
    #     if not line:
    #         return None
        
    #     answer_value = None

    #     if line.suggested_answer_id:
    #         answer_value = (
    #             line.suggested_answer_id.value or ''
    #         ).strip().lower()

    #     elif line.value_char_box:
    #         answer_value = (
    #             line.value_char_box or ''
    #         ).strip().lower()

    #     elif line.value_numerical_box not in (None, False):
    #         answer_value = str(
    #             line.value_numerical_box
    #         ).strip().lower()
        
    #     _logger.warning('Valor de respuesta para pregunta_seq=%s en user_input_id=%s: %s', question_seq, user_input.id, answer_value)
    #     return answer_value

    def _get_answer_value_from_line(self, line):
        """
        Devuelve el valor normalizado de respuesta.
        """
        # Múltiple choice
        if line.suggested_answer_id:
            return (line.suggested_answer_id.value or '').strip().lower()

        # Texto libre
        if line.value_char_box:
            return line.value_char_box.strip().lower()

        # Numérico
        if line.value_numerical_box is not None:
            return str(line.value_numerical_box).strip().lower()

        return None

    def _count_max_score(self, inputs):

        if not inputs:
            return 0

        survey = inputs[0].survey_id
        indicator_question = self.env['survey.question'].search([
            ('survey_id', '=', survey.id),
            ('dashboard_feedback_type', '=', 'max_score_indicator'),
        ], limit=1)

        if not indicator_question:
            return 0

        scores = []
        for inp in inputs:
            line = inp.user_input_line_ids.filtered(
                lambda l: l.question_id.id == indicator_question.id
            )
            if not line:
                continue
            line = line[0]
            val = None
            if line.suggested_answer_id:
                val = line.suggested_answer_id.value
            elif line.value_numerical_box is not None:
                val = line.value_numerical_box
            elif line.value_char_box:
                val = line.value_char_box

            if val is not None:
                try:
                    scores.append(float(val))
                except (ValueError, TypeError):
                    pass

        if not scores:
            return 0

        max_val = max(scores)
        return sum(1 for s in scores if s == max_val)
    
    def _classify_results(self, inputs):

        positive = neutral = negative = 0

        for inp in inputs:
            compliment_hit = False
            complaint_hit = False

            for line in inp.user_input_line_ids:
                question = line.question_id

                if not question.dashboard_feedback_type:
                    continue

                value = self._get_answer_value_from_line(line)

                if value is None:
                    continue

                trigger_value = (question.dashboard_trigger_value or '').strip().lower()

                value = value.strip().lower()
                matched = value == trigger_value

                if (question.dashboard_feedback_type == 'compliment' and matched):
                    compliment_hit = True
                elif (question.dashboard_feedback_type == 'complaint' and matched):
                    complaint_hit = True

            if compliment_hit and not complaint_hit:
                positive += 1
            elif complaint_hit and not compliment_hit:
                negative += 1
            else:
                neutral += 1

        return positive, neutral, negative

    # def _classify_results(self, inputs):
    #     """
    #     Clasifica los resultados como positivo, neutro o negativo:
    #     - Positivo: pregunta 5 = yes  Y  pregunta 7 = no/N/A
    #     - Negativo: pregunta 7 = yes  Y  pregunta 5 = no/N/A
    #     - Neutro:   cualquier otra combinación
    #     """
    #     positive = neutral = negative = 0
    #     for inp in inputs:
    #         v5 = self._get_answer_value(inp, question_seq=14) or ''
    #         v7 = self._get_answer_value(inp, question_seq=16) or ''
    #         v5_yes = v5.lower() == 'yes'
    #         v7_yes = v7.lower() == 'yes'
    #         v5_neg = v5.lower() in ('no', 'n/a', '')
    #         v7_neg = v7.lower() in ('no', 'n/a', '')

    #         if v5_yes and v7_neg:
    #             positive += 1
    #         elif v7_yes and v5_neg:
    #             negative += 1
    #         else:
    #             neutral += 1
    #     return positive, neutral, negative

    def _top_tags(self, inputs, field_name, limit=5):
        """Devuelve los top tags más seleccionados"""
        lang = self.env.user.lang or 'en_US'
        counter = Counter()
        for inp in inputs:
            for tag in getattr(inp, field_name).with_context(lang=lang):
                counter[tag.name] += 1
        return counter.most_common(limit)

    def _top_person_by_tag(self, inputs, person_field, tag_field, limit=5):
        """
        Devuelve el top de personas (auditor/coordinador) que aparecen en registros
        que tienen al menos un tag en el campo indicado.
        """
        counter = Counter()
        for inp in inputs:
            tags = getattr(inp, tag_field)
            if tags:
                person = getattr(inp, person_field) or ''
                if person:
                    counter[person] += len(tags)
        return counter.most_common(limit)




class SurveyExtended(Survey):

    @http.route('/survey/submit/<string:survey_token>/<string:answer_token>', type='json', auth='public', website=True)
    def survey_submit(self, survey_token, answer_token, **post):
        """ Submit a page from the survey.
        This will take into account the validation errors and store the answers to the questions.
        If the time limit is reached, errors will be skipped, answers will be ignored and
        survey state will be forced to 'done'.
        Also returns the correct answers if the scoring type is 'scoring_with_answers_after_page'."""
        # Survey Validation
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return {}, {'error': access_data['validity_code']}
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']

        if answer_sudo.state == 'done':
            return {}, {'error': 'unauthorized'}

        questions, page_or_question_id = survey_sudo._get_survey_questions(answer=answer_sudo,page_id=post.get('page_id'),question_id=post.get('question_id'))

        if (
            not answer_sudo.test_entry
            and not answer_sudo.imported_from_file
            and not survey_sudo._has_attempts_left(
                answer_sudo.partner_id,
                answer_sudo.email,
                answer_sudo.invite_token
            )
        ):  
            # prevent cheating with users creating multiple 'user_input' before their last attempt
            return {}, {'error': 'unauthorized'}
        
        if answer_sudo.survey_time_limit_reached or answer_sudo.question_time_limit_reached:
            if answer_sudo.question_time_limit_reached:
                time_limit = survey_sudo.session_question_start_time + relativedelta(
                    seconds=survey_sudo.session_question_id.time_limit
                )
                time_limit += timedelta(seconds=3)
            else:
                time_limit = answer_sudo.start_datetime + timedelta(minutes=survey_sudo.time_limit)
                time_limit += timedelta(seconds=10)
            if fields.Datetime.now() > time_limit:
                # prevent cheating with users blocking the JS timer and taking all their time to answer
                return {}, {'error': 'unauthorized'}

        errors = {}
        # Prepare answers / comment by question, validate and save answers
        for question in questions:
            inactive_questions = request.env['survey.question'] if answer_sudo.is_session_answer else answer_sudo._get_inactive_conditional_questions()
            if question in inactive_questions:  # if question is inactive, skip validation and save
                continue
            answer, comment = self._extract_comment_from_answers(question, post.get(str(question.id)))
            errors.update(question.validate_question(answer, comment))
            if not errors.get(question.id):
                answer_sudo._save_lines(question, answer, comment, overwrite_existing=survey_sudo.users_can_go_back or question.save_as_nickname or question.save_as_email)

        if errors and not (answer_sudo.survey_time_limit_reached or answer_sudo.question_time_limit_reached):
            return {}, {'error': 'validation', 'fields': errors}

        if not answer_sudo.is_session_answer:
            answer_sudo._clear_inactive_conditional_answers()

        # Get the page questions correct answers if scoring type is scoring after page
        correct_answers = {}
        if survey_sudo.scoring_type == 'scoring_with_answers_after_page':
            scorable_questions = (questions - answer_sudo._get_inactive_conditional_questions()).filtered('is_scored_question')
            correct_answers = scorable_questions._get_correct_answers()

        if answer_sudo.survey_time_limit_reached or survey_sudo.questions_layout == 'one_page':
            answer_sudo._mark_done()
        elif 'previous_page_id' in post:
            # when going back, save the last displayed to reload the survey where the user left it.
            answer_sudo.last_displayed_page_id = post['previous_page_id']
            # Go back to specific page using the breadcrumb. Lines are saved and survey continues
            return correct_answers, self._prepare_question_html(survey_sudo, answer_sudo, **post)
        elif 'next_skipped_page_or_question' in post:
            answer_sudo.last_displayed_page_id = page_or_question_id
            return correct_answers, self._prepare_question_html(survey_sudo, answer_sudo, next_skipped_page=True)
        else:
            if not answer_sudo.is_session_answer:
                page_or_question = request.env['survey.question'].sudo().browse(page_or_question_id)
                if answer_sudo.survey_first_submitted and answer_sudo._is_last_skipped_page_or_question(page_or_question):
                    next_page = request.env['survey.question']
                else:
                    next_page = survey_sudo._get_next_page_or_question(answer_sudo, page_or_question_id)
                if not next_page:
                    if survey_sudo.users_can_go_back and answer_sudo.user_input_line_ids.filtered(
                            lambda a: a.skipped and a.question_id.constr_mandatory):
                        answer_sudo.write({
                            'last_displayed_page_id': page_or_question_id,
                            'survey_first_submitted': True,
                        })
                        return correct_answers, self._prepare_question_html(survey_sudo, answer_sudo, next_skipped_page=True)
                    else:
                        answer_sudo._mark_done()

            answer_sudo.last_displayed_page_id = page_or_question_id

        return correct_answers, self._prepare_question_html(survey_sudo, answer_sudo)