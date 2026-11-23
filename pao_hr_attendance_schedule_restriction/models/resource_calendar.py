from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    attendance_restrict_schedule = fields.Boolean(
        string="Restrict Check-in/Check-out to Schedule",
        default=True,
        help="If enabled, employees using this working schedule can only check in "
             "and check out from the attendance button (systray, mobile app or kiosk) "
             "within the periods of the schedule and the tolerances below.",
    )
    attendance_checkin_tolerance = fields.Integer(
        string="Minutes Allowed Before Check-in",
        default=10,
        help="How many minutes before the start of each period (Morning/Afternoon) "
             "the employee may check in. Late check-ins are allowed until the period ends.",
    )
    attendance_checkout_tolerance = fields.Integer(
        string="Minutes Allowed After Check-out",
        default=5,
        help="How many minutes after the end of the period the employee may still check out. "
             "Early check-outs are always allowed.",
    )

    @api.constrains("attendance_checkin_tolerance", "attendance_checkout_tolerance")
    def _check_attendance_tolerances(self):
        for calendar in self:
            if calendar.attendance_checkin_tolerance < 0 or calendar.attendance_checkout_tolerance < 0:
                raise ValidationError(_("Attendance tolerances cannot be negative."))
