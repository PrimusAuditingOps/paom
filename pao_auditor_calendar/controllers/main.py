from datetime import datetime, timedelta
import uuid
import pytz

import json
from odoo.exceptions import ValidationError
from odoo import http, _
from odoo.http import request
from logging import getLogger
from odoo.addons.web.controllers.main import content_disposition

_logger = getLogger(__name__)

class WebsiteAuditorCalendar(http.Controller):
    
    def _get_portal_status(self):
        statuses_colors = ['transparent', 'Red', 'Orange', 'Yellow', 'Cyan', 'Purple',
                        'Almond', 'Teal', 'Blue', 'Raspberry', 'Green', 'Violet']
        
        portal_audit_status = request.env['auditconfirmation.auditstate'].sudo().search([("show_in_portal", "=", True)])
        statuses = []
        
        for status in portal_audit_status:
            statuses.append({
                'id': status.id,
                'name': status.name,
                'color': statuses_colors[status.color]
            })
        
        return statuses
    
    @http.route('/auditor_agenda/get_events', type='json', auth='user')
    def get_events(self):
        
        partner = request.env.user.partner_id
        portal_audit_status = request.env['auditconfirmation.auditstate'].sudo().search([("show_in_portal", "=", True)])
        statuses_colors = ['transparent', 'Red', 'Orange', 'Yellow', 'Cyan', 'Purple',
                        'Almond', 'Teal', 'Blue', 'Raspberry', 'Green', 'Violet']
        
        purchase_orders = request.env['purchase.order'].sudo().search(
            [
                ('state', '!=', 'cancel'), 
                ('ac_audit_status', 'in', portal_audit_status.ids),
                ('partner_id', '=', partner.id),
            ]
        )
        
        purchase_orders = purchase_orders.filtered(lambda po: po.ac_audit_confirmation_status in ['1', '3'])
        
        events = []
        for order in purchase_orders:
            
            order_lines_data = []
            
            min_start_date = datetime.max.date()
            max_end_date = datetime.min.date()
            
            for line in order.order_line:
                if line.service_start_date and line.service_start_date < min_start_date:
                    min_start_date = line.service_start_date
                if line.service_end_date and line.service_end_date > max_end_date:
                    max_end_date = line.service_end_date
                
                order_lines_data.append({
                    'description': line.name,
                    'organization': line.organization_id.name if line.organization_id else '',
                    'registry_number': line.registrynumber_id.name if line.registrynumber_id else '',
                    'start_date': line.service_start_date,
                    'end_date': line.service_end_date
                })
                    
            events.append({
                'id': str(uuid.uuid4()),
                'title': order.display_name,
                'start': min_start_date,
                'end': max_end_date + timedelta(days=1), # End date that FullCalendar will consider for creating and displaying the event on the calendar; one day is added because the calendar takes the end date with a time of 12 AM, which results in the event ending at the beginning of that end day instead of showing it in its entirety.
                'display_end_date': max_end_date + timedelta(days=1), # End date to be displayed in the event details; one day is added because when creating a Date object, one day is subtracted.
                'backgroundColor': statuses_colors[order.ac_audit_status.color],
                'order_lines': order_lines_data,
                'type': order.ac_audit_status.name,
                'city': order.audit_city_id.name,
                'customer': order.sale_order_id.partner_id.name if order.sale_order_id else '',
                'coordinator': order.coordinator_id.name,
                'auditor_availability': order.ac_audit_confirmation_status,
                'ra_download_link': '/auditor_agenda/download_ra/' + str(order.id),
                'state': order.audit_state_id.name,
                'allDay': True,
                'editable': False,
            })
        
        auditor_days_off = request.env['auditordaysoff.days'].sudo().search(
            [('auditor_id', '=', partner.id)],
            order='start_date ASC',
        )
        
        for days_off in auditor_days_off:
            events.append({
                'id': str(uuid.uuid4()),
                'odoo_id': str(days_off.id),
                'title': days_off.name,
                'start': days_off.start_date,
                'end': days_off.end_date + timedelta(days=1), # End date that FullCalendar will consider for creating and displaying the event on the calendar; one day is added because the calendar takes the end date with a time of 12 AM, which results in the event ending at the beginning of that end day instead of showing it in its entirety.
                'display_end_date': days_off.end_date + timedelta(days=1), # End date to be displayed in the event details; one day is added because when creating a Date object, one day is subtracted.
                'backgroundColor': '#ababab',
                'comments': days_off.comments if days_off.comments else _('N/A'),
                'type': 'days_off',
                'editable_event': self._is_event_editable(days_off.start_date, days_off.end_date),
                'allDay': True,
                'editable': False,
            })
            
        return events
    
    def _is_event_editable(self, start_date, end_date):
        tz = pytz.timezone('America/Mexico_City')
        current_date = datetime.now(tz).date()
        
        if current_date < start_date:
            return 1
        elif start_date <= current_date <= end_date:
            return 0
        
        return 0
    
    @http.route(['/auditor_agenda'], type='http', auth="user", website=True)
    def auditor_agenda(self, **kwargs):

        start_date = kwargs.get("start_date", datetime.today().strftime('%Y-%m'))
        statuses = self._get_portal_status()
        
        lang = request.env.context.get('lang')
        return request.render("pao_auditor_calendar.auditor_agenda_calendar_portal_view", 
            {
                'page_name': 'auditor_agenda',
                'lang': lang, 
                'statuses': statuses,
                'start_date': start_date
            }
        )
    
    def _check_purchase_order_lines(self, partner_id, start_date, end_date):
        overlapping_order_lines = request.env['purchase.order.line'].search([
            ('partner_id', '=', partner_id),
            ('state', '!=', 'cancel'),  # Ignore canceled orders
            ('service_start_date', '<=', end_date),
            ('service_end_date', '>=', start_date)
        ])
        
        return overlapping_order_lines
    
    @http.route(['/auditor_agenda/set_days_off'], type='json', methods=['POST'], auth="user", website=True)
    def add_days_off(self, **kwargs):

        data = json.loads(request.httprequest.data) 
        summary = data.get("summary")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        comments = data.get("comments")
        dayoff_id = data.get("dayoff_id") if data.get("dayoff_id") else None
        partner_id = request.env.user.partner_id.id
        
        overlapping_order_lines = self._check_purchase_order_lines(partner_id, start_date, end_date)

        tz = pytz.timezone('America/Mexico_City')
        current_date = datetime.now(tz).date()
        format_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        format_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if format_end_date < format_start_date:
            return {'error': _('Invalid dates.')}

        if format_start_date < current_date:
            return {'error': _('You cannot create an event on a date that has already passed.')}
        
        values = {
            'name': summary,
            'start_date': start_date,
            'end_date': end_date,
            'comments': comments,
        }

        if not overlapping_order_lines:
            if dayoff_id and dayoff_id != '':
                daysoff_record = request.env['auditordaysoff.days'].sudo().browse(int(dayoff_id))
                daysoff_record.write(values)
            else:
                values['auditor_id'] = partner_id
                request.env['auditordaysoff.days'].sudo().create(values)
        else:
            return {'error': _("The auditor has audit events on the selected dates.")}
        
        return {'success': True}
    
    @http.route(['/auditor_agenda/delete_days_off'], type='json', methods=['POST'], auth="user", website=True)
    def delete_days_off(self, **kwargs):

        data = json.loads(request.httprequest.data) 
        dayoff_id = data.get("dayoff_id") if data.get("dayoff_id") else None
        
        daysoff_record = request.env['auditordaysoff.days'].sudo().browse(int(dayoff_id))
        if not daysoff_record.exists():
            return {'error': _('Record not found.')}
        
        daysoff_record.unlink()
        return {'success': True}

    @http.route('/auditor_agenda/download_ra/<int:id>', type='http', auth="user", website=True)
    def calendar_download_ra(self, id=None, **kwargs):

        order_sudo = request.env['purchase.order'].sudo().search([('id', '=', id)])
        rafilename = 'RA-'+order_sudo.name+'-'+order_sudo.partner_id.name+'.pdf'
        
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'servicereferralagreement.report_rapurchaseorder',
            id,
        )[0]
        
        return request.make_response(pdf, [('Content-Type', 'application/octet-stream'), ('Content-Disposition', content_disposition(rafilename))])