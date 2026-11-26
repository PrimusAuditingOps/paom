from datetime import datetime, time, timedelta

import pytz

from odoo import _, fields, models
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_action_change(self, geo_information=None):
        """Self-service check-in/check-out (systray, mobile app and kiosk)."""
        self.ensure_one()
        employee = self.sudo()
        now = fields.Datetime.now()
        if employee.attendance_state != "checked_in":
            error = employee._get_attendance_checkin_error(now)
        else:
            attendance = self.env["hr.attendance"].sudo().search(
                [("employee_id", "=", employee.id), ("check_out", "=", False)], limit=1
            )
            # Without an open attendance the native method raises its own error.
            error = attendance and employee._get_attendance_checkout_error(attendance.check_in, now)
        if error:
            raise UserError("%s\n\n%s" % (error, _(
                "Ask %(manager)s to register it for you.",
                manager=employee.attendance_manager_id.name or _("your attendance manager"),
            )))
        return super(
            HrEmployee, self.with_context(attendance_self_service=True)
        )._attendance_action_change(geo_information)

    # ------------------------------------------------------------------
    # Schedule helpers (shared by self-service and manager capture)
    # ------------------------------------------------------------------
    def _attendance_tz(self):
        self.ensure_one()
        return pytz.timezone(self.tz or self.resource_calendar_id.tz or "UTC")

    def _attendance_to_local(self, utc_dt):
        return pytz.utc.localize(utc_dt).astimezone(self._attendance_tz()).replace(tzinfo=None)

    def _get_attendance_schedule_periods(self, calendar, day):
        """Working periods (Morning/Afternoon, never Break) of ``day`` as a sorted
        list of naive local datetimes ``(start, end)``."""
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
        return sorted(
            (day_start + timedelta(hours=line.hour_from), day_start + timedelta(hours=line.hour_to))
            for line in calendar.attendance_ids.filtered(_applies)
        )

    @staticmethod
    def _format_attendance_windows(windows):
        return ", ".join(
            "%s - %s" % (start.strftime("%H:%M"), end.strftime("%H:%M")) for start, end in windows
        )

    def _get_attendance_calendar_error(self):
        self.ensure_one()
        if not self.resource_calendar_id:
            return _(
                "%(name)s has no working schedule assigned, so the attendance cannot be registered.",
                name=self.name,
            )
        return False

    def _get_attendance_checkin_error(self, check_in, exclude_attendance_id=False):
        """Return an error message if ``check_in`` (naive UTC) is not allowed, else False."""
        self.ensure_one()
        employee = self.sudo()
        error = employee._get_attendance_calendar_error()
        if error:
            return error
        calendar = employee.resource_calendar_id
        if not calendar.attendance_restrict_schedule:
            return False

        local = employee._attendance_to_local(check_in)
        periods = employee._get_attendance_schedule_periods(calendar, local.date())
        if not periods:
            return _(
                "%(date)s is not a working day in the schedule \"%(calendar)s\" of %(name)s, "
                "so no check-in can be registered.",
                date=local.strftime("%d/%m/%Y"),
                calendar=calendar.name,
                name=employee.name,
            )
        before = timedelta(minutes=calendar.attendance_checkin_tolerance)
        late = timedelta(minutes=calendar.attendance_late_tolerance)
        windows = [(start - before, start + late) for start, _end in periods]
        if not any(start <= local <= end for start, end in windows):
            return _(
                "A check-in at %(time)s is not allowed. Allowed check-in times on %(date)s: "
                "%(windows)s.",
                time=local.strftime("%H:%M"),
                date=local.strftime("%d/%m/%Y"),
                windows=self._format_attendance_windows(windows),
            )

        min_break = timedelta(minutes=calendar.attendance_min_break)
        if min_break:
            domain = [
                ("employee_id", "=", employee.id),
                ("check_out", "!=", False),
                ("check_out", "<=", check_in),
            ]
            if exclude_attendance_id:
                domain.append(("id", "!=", exclude_attendance_id))
            last = self.env["hr.attendance"].sudo().search(domain, order="check_out desc", limit=1)
            if last and check_in < last.check_out + min_break:
                return _(
                    "At least %(minutes)s minutes must pass between the last check-out "
                    "(%(last)s) and the next check-in. Check-in is allowed from %(allowed)s.",
                    minutes=calendar.attendance_min_break,
                    last=employee._attendance_to_local(last.check_out).strftime("%H:%M"),
                    allowed=employee._attendance_to_local(last.check_out + min_break).strftime("%H:%M"),
                )
        return False

    def _get_attendance_checkout_error(self, check_in, check_out):
        """Return an error message if ``check_out`` (naive UTC) is not allowed for an
        attendance that started at ``check_in`` (naive UTC), else False."""
        self.ensure_one()
        employee = self.sudo()
        error = employee._get_attendance_calendar_error()
        if error:
            return error
        calendar = employee.resource_calendar_id
        if not calendar.attendance_restrict_schedule:
            return False

        before = timedelta(minutes=calendar.attendance_checkin_tolerance)
        after = timedelta(minutes=calendar.attendance_checkout_tolerance)
        check_in_local = employee._attendance_to_local(check_in)
        check_out_local = employee._attendance_to_local(check_out)

        # Period the attendance belongs to (the one its check-in fell into).
        periods = employee._get_attendance_schedule_periods(calendar, check_in_local.date())
        period = next(
            ((start, end) for start, end in periods if start - before <= check_in_local < end + after),
            None,
        )
        if period:
            limit = period[1] + after
            if check_out_local <= limit:
                return False
            return _(
                "A check-out at %(time)s is not allowed: the limit for this period is %(limit)s.",
                time=check_out_local.strftime("%d/%m/%Y %H:%M"),
                limit=limit.strftime("%d/%m/%Y %H:%M"),
            )

        # The check-in does not match any period (e.g. edited by an administrator):
        # only allow a check-out inside one of the periods of that day.
        windows = [
            (start - before, end + after)
            for start, end in employee._get_attendance_schedule_periods(calendar, check_out_local.date())
        ]
        if any(start <= check_out_local <= end for start, end in windows):
            return False
        return _(
            "A check-out at %(time)s is not allowed because it is outside the working schedule.",
            time=check_out_local.strftime("%d/%m/%Y %H:%M"),
        )
