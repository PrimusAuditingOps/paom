from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    attendance_restrict_schedule = fields.Boolean(
        string="Restrict Check-in/Check-out to Schedule",
        default=True,
        help="If enabled, check-ins and check-outs of employees using this working schedule "
             "must fall within the periods of the schedule and the tolerances below. This "
             "applies to the attendance button (systray, mobile app or kiosk) and to records "
             "captured by the attendance manager. Attendance administrators are not restricted "
             "when editing records.",
    )
    attendance_checkin_tolerance = fields.Integer(
        string="Minutes Allowed Before Check-in",
        default=10,
        help="How many minutes before the start of each period (Morning/Afternoon) "
             "the employee may check in.",
    )
    attendance_late_tolerance = fields.Integer(
        string="Late Check-in Tolerance (minutes)",
        default=10,
        help="How many minutes after the start of each period (Morning/Afternoon) the employee "
             "may still check in. After that, the check-in is blocked.",
    )
    attendance_checkout_tolerance = fields.Integer(
        string="Minutes Allowed After Check-out",
        default=5,
        help="How many minutes after the end of the period the employee may still check out. "
             "Early check-outs are always allowed.",
    )
    attendance_min_break = fields.Integer(
        string="Minimum Break Between Check-out and Check-in (minutes)",
        default=60,
        help="Minimum time that must pass between a check-out and the next check-in "
             "(e.g. the lunch break between the morning and the afternoon).",
    )

    @api.constrains(
        "attendance_checkin_tolerance",
        "attendance_late_tolerance",
        "attendance_checkout_tolerance",
        "attendance_min_break",
    )
    def _check_attendance_tolerances(self):
        for calendar in self:
            if min(
                calendar.attendance_checkin_tolerance,
                calendar.attendance_late_tolerance,
                calendar.attendance_checkout_tolerance,
                calendar.attendance_min_break,
            ) < 0:
                raise ValidationError(_("Attendance tolerances cannot be negative."))
