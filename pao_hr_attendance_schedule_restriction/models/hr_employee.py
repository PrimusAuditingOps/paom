from datetime import datetime, time, timedelta

import pytz

from odoo import _, fields, models
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_action_change(self, geo_information=None):
        """Self-service check-in/check-out (systray, mobile app and kiosk).

        Manual records created or edited from the Attendances app by an attendance
        manager / administrator do not go through this method, so they are not
        restricted by the schedule.
        """
        self.ensure_one()
        self._check_attendance_schedule_window()
        return super(
            HrEmployee, self.with_context(attendance_self_service=True)
        )._attendance_action_change(geo_information)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_attendance_schedule_periods(self, calendar, day):
        """Return the working periods (Morning/Afternoon, never Break) of ``day``
        as a sorted list of naive local datetimes ``(start, end)``."""
        self.ensure_one()
        weekday = str(day.weekday())
        week_type = str(self.env["resource.calendar.attendance"].get_week_type(day))
        resource = self.resource_id

        def _applies(line):
            return (
                not line.display_type
                and line.day_period != "lunch"
                and line.dayofweek == weekday
                and (not line.resource_id or line.resource_id == resource)
                and (not calendar.two_weeks_calendar or line.week_type == week_type)
                and (not line.date_from or line.date_from <= day)
                and (not line.date_to or line.date_to >= day)
            )

        day_start = datetime.combine(day, time.min)
        periods = [
            (day_start + timedelta(hours=line.hour_from), day_start + timedelta(hours=line.hour_to))
            for line in calendar.attendance_ids.filtered(_applies)
        ]
        return sorted(periods)

    @staticmethod
    def _format_attendance_windows(windows):
        return ", ".join(
            "%s - %s" % (start.strftime("%H:%M"), end.strftime("%H:%M")) for start, end in windows
        )

    def _check_attendance_schedule_window(self):
        self.ensure_one()
        employee = self.sudo()
        calendar = employee.resource_calendar_id
        if not calendar:
            raise UserError(_(
                "%(name)s has no working schedule assigned, so the attendance cannot be "
                "registered. Please contact your attendance manager.",
                name=employee.name,
            ))
        if not calendar.attendance_restrict_schedule:
            return

        tz = pytz.timezone(employee.tz or calendar.tz or "UTC")

        def _to_local(utc_dt):
            return pytz.utc.localize(utc_dt).astimezone(tz).replace(tzinfo=None)

        now_local = _to_local(fields.Datetime.now())
        before = timedelta(minutes=calendar.attendance_checkin_tolerance)
        after = timedelta(minutes=calendar.attendance_checkout_tolerance)
        manager_name = employee.attendance_manager_id.name or _("your attendance manager")

        # ---------------- Check-in ----------------
        if employee.attendance_state != "checked_in":
            periods = employee._get_attendance_schedule_periods(calendar, now_local.date())
            if not periods:
                raise UserError(_(
                    "Today is not a working day in your schedule \"%(calendar)s\", so you "
                    "cannot check in. If you need to register an attendance, ask %(manager)s.",
                    calendar=calendar.name,
                    manager=manager_name,
                ))
            windows = [(start - before, end) for start, end in periods]
            if not any(start <= now_local <= end for start, end in windows):
                raise UserError(_(
                    "You cannot check in at this time (%(now)s). Allowed check-in times "
                    "today: %(windows)s.",
                    now=now_local.strftime("%H:%M"),
                    windows=self._format_attendance_windows(windows),
                ))
            return

        # ---------------- Check-out ----------------
        attendance = self.env["hr.attendance"].sudo().search(
            [("employee_id", "=", employee.id), ("check_out", "=", False)], limit=1
        )
        if not attendance:
            # Let the native method raise its own error.
            return

        check_in_local = _to_local(attendance.check_in)
        periods = employee._get_attendance_schedule_periods(calendar, check_in_local.date())
        # Period the open attendance belongs to (the one its check-in fell into).
        period = next(
            ((start, end) for start, end in periods if start - before <= check_in_local < end + after),
            None,
        )
        if period:
            limit = period[1] + after
            if now_local <= limit:
                return
            raise UserError(_(
                "You can no longer check out: the limit for this period was %(limit)s. "
                "Ask %(manager)s to register your check-out.",
                limit=limit.strftime("%d/%m/%Y %H:%M"),
                manager=manager_name,
            ))

        # The open attendance does not match any period (e.g. created manually at an
        # unusual time): only allow checking out inside one of today's periods.
        today_windows = [
            (start - before, end + after)
            for start, end in employee._get_attendance_schedule_periods(calendar, now_local.date())
        ]
        if any(start <= now_local <= end for start, end in today_windows):
            return
        raise UserError(_(
            "You cannot check out at this time (%(now)s) because it is outside your working "
            "schedule. Ask %(manager)s to register your check-out.",
            now=now_local.strftime("%H:%M"),
            manager=manager_name,
        ))
