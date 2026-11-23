from odoo import SUPERUSER_ID, api, fields, models

TRACKED_FIELDS = {"employee_id", "check_in", "check_out"}


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

    def _attendance_track_other_user(self):
        """Whether changes in the current environment should be flagged."""
        return not self.env.context.get("attendance_self_service") and self.env.uid != SUPERUSER_ID

    @api.model_create_multi
    def create(self, vals_list):
        if self._attendance_track_other_user():
            Employee = self.env["hr.employee"].sudo()
            for vals in vals_list:
                employee = Employee.browse(vals.get("employee_id"))
                if employee and employee.user_id != self.env.user:
                    vals["registered_by_other"] = True
                    vals["registered_by_other_user_id"] = self.env.uid
        return super().create(vals_list)

    def write(self, vals):
        to_flag = self.browse()
        if TRACKED_FIELDS & set(vals) and self._attendance_track_other_user():
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
