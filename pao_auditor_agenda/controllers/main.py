from datetime import datetime
import calendar as cal
from dateutil.relativedelta import relativedelta
import pytz
from babel.dates import format_datetime, format_date
import base64
from werkzeug.urls import url_encode

from odoo import http, _, fields
from odoo.http import request
from odoo.tools import html2plaintext, DEFAULT_SERVER_DATETIME_FORMAT as dtf
from odoo.tools.misc import get_lang
from logging import getLogger
from odoo.addons.web.controllers.main import content_disposition
from functools import reduce

_logger = getLogger(__name__)


class WebsiteAuditorCalendar(http.Controller):

    @http.route(['/calendar/auditordates'], type='http', auth="user", website=True)
    def calendar_appointment(self, startdate=None, failed=False, **kwargs):
        status_color = ['transparent', 'Red', 'Orange', 'Yellow', 'Light blue', 'Dark purple',
                        'Salmon pink', 'Medium blue', 'Dark blue', 'Fushia', 'Green', 'Purple']
        #Employee = request.env['hr.employee'].sudo().browse(int(employee_id)) if employee_id else None
        requested_tz = pytz.timezone('America/Mexico_City')
        #today = requested_tz.fromutc(datetime.utcnow())
        if startdate is not None:
            today = datetime.fromisoformat(startdate)
        else:
            today = requested_tz.fromutc(datetime.utcnow())

        last_day = today.date()
        partner = request.env.user.partner_id
        audit_status_ids = []
        order_id_partner = []
        order_id_confirmed = []

        domain = [("show_in_portal", "=", True)]
        audit_status = request.env['auditconfirmation.auditstate'].sudo().search(
            domain,
        )
        for recstatus in audit_status:
            audit_status_ids.append(recstatus.id)

        domain = [('state', '!=', 'cancel'), ('ac_audit_status', 'in', audit_status_ids),
                  ('service_end_date', '>=', today), ('partner_id', '=', partner.id)]
        result_order = request.env['purchase.order.line'].search(
            domain
        )
        for rec_order in result_order:
            order_id_partner.append(rec_order.order_id.id)

        domain = [('ac_id_purchase', 'in', order_id_partner),
                  ('ac_audit_confirmation_status', 'in', ['1', '3'])]
        result_confirmation = request.env['auditconfirmation.purchaseconfirmation'].sudo().search(
            domain
        )
        for rec_confirmation in result_confirmation:
            order_id_confirmed.append(rec_confirmation.ac_id_purchase)

        domain = [('state', '!=', 'cancel'), ('ac_audit_status', 'in', audit_status_ids),
                  ('service_end_date', '>=', today), ('partner_id', '=', partner.id),
                  ('order_id', 'in', order_id_confirmed)]
        result_line_audit = request.env['purchase.order.line'].search(
            domain,
            order='service_start_date ASC',
        )

        if result_line_audit:
            last_day_audit = sorted(result_line_audit, key=lambda x: x.service_end_date, reverse=True)[
                0]["service_end_date"]
            last_day = last_day_audit if last_day_audit else last_day

        domain = [('state', 'not in', ['cancel']), ('ac_audit_status', 'in', audit_status_ids),
                  ('service_end_date', '>=', today), ('shadow_id', '=', partner.id)]
        result_line_shadow = request.env['purchase.order.line'].sudo().search(
            domain,
            order='service_start_date ASC',
        )
        if result_line_shadow:
            last_day_shadow = sorted(result_line_shadow, key=lambda x: x.service_end_date, reverse=True)[
                0]["service_end_date"]
            last_day = last_day_shadow if last_day_shadow and last_day_shadow > last_day else last_day

        domain = [('state', 'not in', ['cancel']), ('ac_audit_status', 'in', audit_status_ids),
                  ('service_end_date', '>=', today), ('assessment_id', '=', partner.id)]
        result_line_assessment = request.env['purchase.order.line'].sudo().search(
            domain,
            order='service_start_date ASC',
        )
        if result_line_assessment:
            last_day_assessment = sorted(
                result_line_assessment, key=lambda x: x.service_end_date, reverse=True)[0]["service_end_date"]
            last_day = last_day_assessment if last_day_assessment and last_day_assessment > last_day else last_day

        current_company = request.env.user.company_id

        status_list = []
        for status_id in audit_status_ids:
            total = 0

            res_audits_status = filter(
                lambda x: x['ac_audit_status'].id == status_id and x['company_id'] == current_company.id, 
                result_line_audit
            )
            total_audit = reduce(
                lambda acc, element: acc + int(element['product_qty']), res_audits_status, 0
            )
            
            res_shadow_status = filter(
                lambda x: x['ac_audit_status'].id == status_id and x['company_id'] == current_company.id, 
                result_line_shadow
            )
            total_shadow = reduce(
                lambda acc, element: acc + int(element['product_qty']), res_shadow_status, 0
            )
            
            res_assessment_status = filter(
                lambda x: x['ac_audit_status'].id == status_id and x['company_id'] == current_company.id, 
                result_line_assessment
            )
            total_assessment = reduce(
                lambda acc, element: acc + int(element['product_qty']), res_assessment_status, 0
            )

            total = total_audit + total_assessment + total_shadow

            # Filter statuses for the current company
            res_status = filter(
                lambda x: x['id'] == status_id and x['company_id'] == current_company.id, 
                audit_status
            )
            
            status_name = ""
            sts_color = 0
            for rec in res_status:
                status_name = rec.name
                sts_color = rec.color

            status_list.append({
                'id': status_name, 
                'value': total,
                'color': 'background-color:' + status_color[sts_color] + ';'
            })

        domain = [('auditor_id', '=', partner.id), ('end_date', '>=', today)]
        result_auditor_daysoff = request.env['auditordaysoff.days'].sudo().search(
            domain,
            order='start_date ASC',
        )
        if result_auditor_daysoff:
            last_day_daysoff = sorted(
                result_auditor_daysoff, key=lambda x: x.end_date, reverse=True)[0]["end_date"]
            last_day = last_day_daysoff if last_day_daysoff and last_day_daysoff > last_day else last_day

        start = today
        month_dates_calendar = cal.Calendar(0).monthdatescalendar
        months = []
        while (start.year, start.month) <= (last_day.year, last_day.month):
            dates = month_dates_calendar(start.year, start.month)
            for week_index, week in enumerate(dates):
                for day_index, day in enumerate(week):
                    mute_cls = today_cls = None
                    weekend_cls = []
                    today_slots = []
                    days_off = []
                    if result_auditor_daysoff and day.month == start.month:
                        days_off = list(filter(
                            lambda x: x['start_date'] <= day and x['end_date'] >= day, result_auditor_daysoff))
                        # Se agregó una descripción a los días no laborales
                    
                        for r in days_off:
                            name = r.name if r.name else 'Day off'
                            comments = r.comments if r.comments else _('No comments')

                            weekend_cls.append({
                                'name': _('Subject: ')+name,
                                'comments':_('Comments: ')+comments,
                                'color': 'background-color:#e9ecef; font-weight:Bold; word-wrap: break-word;'
                            })
                            """
                            weekend_cls.append({
                                'hours': '---------- Comentarios ----------',
                                'url_ra': '',
                                'color': 'background-color: gray ; font-weight:Bold; color:white;'
                            })
                            
                            commentsArray = []
                            
                            commentsSize = len(comments)
                            
                            lyricsPerRow= 30
                            count= int(commentsSize/lyricsPerRow)
                            
                            for i in range(count+1):
                                if count == 0:
                                    commentsArray.append(comments[:commentsSize])
                                elif (i+1)*lyricsPerRow > commentsSize:
                                    commentsArray.append(comments[i*lyricsPerRow:commentsSize])
                                else:
                                    commentsArray.append(comments[i*lyricsPerRow:(i+1)*lyricsPerRow]) 


                            for comment in commentsArray:

                                today_slots.append({
                                    'hours': comment,
                                    'url_ra': '',
                                    'color': 'background-color: gray ; font-weight:Bold; color:white;'
                                })

                            """

                    #if len(days_off) > 0:
                    #    weekend_cls = 'o_weekend'
                    if day == today.date() and day.month == today.month:
                        today_cls = 'o_today'

                    if day.month != start.month:
                        mute_cls = 'text-muted o_mute_day'
                    else:
                        if result_line_audit:
                            lineaudit = filter(
                                lambda x: x['service_start_date'] <= day and x['service_end_date'] >= day, result_line_audit)
                            for r in lineaudit:
                                state = r.order_id.audit_state_id.name if r.order_id.audit_state_id else ''
                                city = r.order_id.audit_city_id.name if r.order_id.audit_city_id else ''
                                status = r.order_id.sudo().ac_audit_status.name if r.order_id.sudo().ac_audit_status else ''
                                description = city + ' ' + state + ' ' + r.name + ' - ' + \
                                    str(r.product_qty)  # + _(' - Status: ') + status

                                today_slots.append({
                                    'hours': description,
                                    'url_ra': '/calendar/download/ra/' + str(r.order_id.id),
                                    'color': 'background-color:' + status_color[r.order_id.sudo().ac_audit_status.color]+'; font-weight:Bold; color:white;'
                                })
                        if result_line_shadow:
                            lineshadow = filter(
                                lambda x: x['service_start_date'] <= day and x['service_end_date'] >= day, result_line_shadow)
                            for r in lineshadow:
                                state = r.order_id.audit_state_id.name if r.order_id.audit_state_id else ''
                                city = r.order_id.audit_city_id.name if r.order_id.audit_city_id else ''
                                description = _(
                                    'Shadow - ')+city + ' ' + state + ' ' + r.name + ' - ' + str(r.product_qty)
                                today_slots.append({
                                    'hours': description,
                                    'url_ra': '',
                                    'color': 'background-color:' + status_color[r.order_id.sudo().ac_audit_status.color]+'; font-weight:Bold; color:white;'
                                })
                        if result_line_assessment:
                            lineassessment = filter(
                                lambda x: x['service_start_date'] <= day and x['service_end_date'] >= day, result_line_assessment)
                            for r in lineassessment:
                                state = r.order_id.audit_state_id.name if r.order_id.audit_state_id else ''
                                city = r.order_id.audit_city_id.name if r.order_id.audit_city_id else ''
                                description = 'Assessment - '+city + ' ' + state + \
                                    ' ' + r.name + ' - ' + str(r.product_qty)
                                today_slots.append({
                                    'hours': description,
                                    'url_ra': '',
                                    'color': 'background-color:' + status_color[r.order_id.sudo().ac_audit_status.color]+'; font-weight:Bold; color:white;'
                                })

                    dates[week_index][day_index] = {
                        'day': day,
                        'slots': today_slots,
                        'mute_cls': mute_cls,
                        'weekend_cls': weekend_cls,
                        'today_cls': today_cls
                    }

            months.append({
                'month': format_datetime(start, 'MMMM Y', locale = request.env.context.get('lang')),
                'weeks': dates
            })
            start = start + relativedelta(months=1)

        return request.render("pao_auditor_agenda.auditor_calendar", {
            # 'appointment_type': appointment_type,
            # 'timezone': request.session['timezone'],
            'failed': failed,
            'slots': months,
            'date': today.date(),
            'statusid': status_list
        })

    @http.route('/calendar/download/ra/<int:id>', type='http', auth="user", website=True)
    def calendar_download_ra(self, id=None, **kwargs):

        domain = [('id', '=', id)]
        order_sudo = request.env['purchase.order'].sudo().search(
            domain
        )
        rafilename = 'RA-'+order_sudo.name+'-'+order_sudo.partner_id.name+'.pdf'

        # pdf = request.env.ref('servicereferralagreement.report_rapurchaseorder').sudo(
        # )._render_qweb_pdf([id])[0]
        
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'servicereferralagreement.report_rapurchaseorder',
            id,
        )[0]
        
        return request.make_response(pdf, [('Content-Type', 'application/octet-stream'), ('Content-Disposition', content_disposition(rafilename))])