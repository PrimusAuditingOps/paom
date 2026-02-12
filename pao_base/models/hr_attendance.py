from odoo import api, fields, models
from datetime import datetime, timedelta
import random


class HelpdeskTicket(models.Model):
    _inherit = 'hr.attendance'

    def set_pao_attendance(self, users_data):

            # users_data = {
            #     9: { #S
            #         'latitude': 24.7598295,
            #         'longitude': -107.2781705,
            #         'ip_address': '177.228.109.0',
            #     },
            #     10: { #H
            #         'latitude': 24.7483090,
            #         'longitude': -107.4371877,
            #         'ip_address': '187.149.121.217',
            #     },
            #     179: { #M
            #         'latitude': 24.7895000,
            #         'longitude': -107.3730000,
            #         'ip_address': '177.228.125.244',
            #     },
            # }
            
            for user_id, data in users_data.items():
                
                now = fields.Datetime.context_timestamp(self.env.user, fields.Datetime.now())

                # Random seconds between 30 and 120
                random_seconds = random.randint(30, 120)

                now_offset = now + timedelta(seconds=random_seconds)

                # If you need to store it in a datetime field:
                now_offset_utc = fields.Datetime.to_string(now_offset)
                
                employee = self.env['hr.employee'].search([
                    ('user_id', '=', user_id)
                ], limit=1)
                
                current_attendance = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('check_out', '=', False)
                ], limit=1)
                
                if not current_attendance:
                    self.env['hr.attendance'].with_user(user_id).create({
                        'employee_id': employee.id,
                        'check_in': now_offset,
                        'in_mode': 'systray',
                        'in_latitude': data['latitude'],
                        'in_longitude': data['longitude'],
                        'in_browser': 'chrome',
                        'in_country_name': 'Mexico',
                        'in_city': 'Culiacán',
                        'in_ip_address': data['ip_address'],
                    })
                else:
                    current_attendance.with_user(user_id).write({
                        # 'employee_id': employee.id,
                        'check_out': now_offset,
                        'out_mode': 'systray',
                        'out_latitude': data['latitude'],
                        'out_longitude': data['longitude'],
                        'out_browser': 'chrome',
                        'out_country_name': 'Mexico',
                        'out_city': 'Culiacán',
                        'out_ip_address': data['ip_address'],
                        'write_uid': user_id,
                    })
