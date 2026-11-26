from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import AccessError, UserError

TIME_FIELDS = {"employee_id", "check_in", "check_out"}


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    registered_by_other = fields.Boolean(
        string="Registered by Another User",
        readonly=True,
        copy=False,
        index=True,
        help="Checked when the check-in/check-out was created or modified by a user "
             "other than the employee (e.g. their attendance manager), instead of the "
             "employee's own check-in/check-out button.",
    )
    registered_by_other_user_id = fields.Many2one(
        "res.users",
        string="Registered/Modified by",
        readonly=True,
        copy=False,
        help="Last user, other than the employee, who created or modified the check-in/check-out.",
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _attendance_is_self_service(self):
        return bool(self.env.context.get("attendance_self_service"))

    def _attendance_is_admin(self):
        """Attendance administrators (and system processes) edit freely."""
        return self.env.su or self.env.user.has_group("hr_attendance.group_hr_attendance_manager")

    def _attendance_is_restricted_capture(self):
        """Manual capture by an attendance manager who is not an administrator."""
        return not self._attendance_is_self_service() and not self._attendance_is_admin()

    def _attendance_track_other_user(self):
        return not self._attendance_is_self_service() and self.env.uid != SUPERUSER_ID

    def _attendance_check_not_future(self, value, now):
        if value and value > now:
            raise UserError(_("You cannot register a check-in or check-out in the future."))

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        Employee = self.env["hr.employee"].sudo()
        restricted = self._attendance_is_restricted_capture()
        track = self._attendance_track_other_user()
        now = fields.Datetime.now()
        for vals in vals_list:
            employee = Employee.browse(vals.get("employee_id") or self.env.user.employee_id.id)
            if restricted and employee:
                check_in = fields.Datetime.to_datetime(vals.get("check_in")) or now
                check_out = fields.Datetime.to_datetime(vals.get("check_out"))
                self._attendance_check_not_future(check_in, now)
                self._attendance_check_not_future(check_out, now)
                error = employee._get_attendance_checkin_error(check_in)
                if not error and check_out:
                    error = employee._get_attendance_checkout_error(check_in, check_out)
                if error:
                    raise UserError(error)
            if track and employee and employee.user_id != self.env.user:
                vals["registered_by_other"] = True
                vals["registered_by_other_user_id"] = self.env.uid
        return super().create(vals_list)

    def write(self, vals):
        touched = TIME_FIELDS & set(vals)
        if touched and self._attendance_is_restricted_capture():
            self._attendance_check_manager_write(vals)

        to_flag = self.browse()
        if touched and self._attendance_track_other_user():
            new_employee = self.env["hr.employee"].sudo().browse(vals.get("employee_id"))
            if new_employee and new_employee.user_id != self.env.user:
                to_flag = self
            else:
                to_flag = self.filtered(lambda att: att.sudo().employee_id.user_id != self.env.user)
        result = super().write(vals)
        if to_flag:
            super(HrAttendance, to_flag.sudo()).write({
                "registered_by_other": True,
                "registered_by_other_user_id": self.env.uid,
            })
        return result

    def _attendance_check_manager_write(self, vals):
        """An attendance manager may only add the missing check-out of an attendance;
        existing check-in/check-out times and the employee cannot be changed."""
        if "employee_id" in vals or "check_in" in vals:
            raise UserError(_(
                "You cannot modify the employee or the check-in time of an existing attendance. "
                "Only an attendance administrator can correct it."
            ))
        check_out = fields.Datetime.to_datetime(vals.get("check_out"))
        now = fields.Datetime.now()
        for attendance in self.sudo():
            if attendance.check_out:
                raise UserError(_(
                    "The attendance of %(name)s already has a check-out. Only an attendance "
                    "administrator can modify it.",
                    name=attendance.employee_id.name,
                ))
            if not check_out:
                continue
            self._attendance_check_not_future(check_out, now)
            error = attendance.employee_id._get_attendance_checkout_error(attendance.check_in, check_out)
            if error:
                raise UserError(error)

    def unlink(self):
        if not self._attendance_is_self_service() and not self._attendance_is_admin():
            raise AccessError(_("Only attendance administrators can delete attendance records."))
        return super().unlink()
