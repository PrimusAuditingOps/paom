from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

# Lo único que se puede modificar de una asignación ya cerrada.
EDITABLE_WHEN_CLOSED = {'notes'}


# ==========================================
# ASIGNACIÓN DE LICENCIA (quién usa la suscripción)
# ==========================================
# A un empleado O a un departamento. Opcional: una suscripción puede no
# tener asignaciones (p. ej. tarifas fijas usadas por varios departamentos).
# Para quitar una asignación se CIERRA con fecha de fin; nunca se borra, así
# se conserva quién tuvo la licencia y cuándo.
class PaoItLicenseAssignment(models.Model):
    _name = 'pao.it.license.assignment'
    _description = 'License Assignment'
    _order = 'date_start desc, id desc'
    _rec_names_search = ['subscription_id.software_id.name', 'employee_id.name', 'department_id.name']

    subscription_id = fields.Many2one('pao.it.subscription', string='Subscription', required=True,
                                      ondelete='cascade', index=True)
    company_id = fields.Many2one(related='subscription_id.company_id', store=True, index=True)
    software_id = fields.Many2one(related='subscription_id.software_id', store=True)
    assignee_type = fields.Selection([
        ('employee', 'Employee'),
        ('department', 'Department'),
    ], string='Assign To', required=True, default='employee')
    employee_id = fields.Many2one('hr.employee', string='Employee', index=True, ondelete='restrict')
    department_id = fields.Many2one('hr.department', string='Department', ondelete='restrict')
    # Departamento del responsable: el del empleado en RR. HH., o el asignado
    # directamente. Guardado para agrupar/filtrar ("licencias de
    # Operaciones", personales + del área). En renglones de departamento es
    # el campo que se captura (y se copia a department_id, ver onchange).
    effective_department_id = fields.Many2one(
        'hr.department', string="Responsible's Department", compute='_compute_effective_department',
        store=True, readonly=False, index=True)
    responsible = fields.Char(string='Responsible', compute='_compute_responsible')
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.context_today)
    date_end = fields.Date(string='End Date')
    state = fields.Selection([
        ('active', 'Active'),
        ('closed', 'Closed'),
    ], string='Status', compute='_compute_state', search='_search_state')
    # Asignación vigente de un empleado ARCHIVADO (baja): hay que revisarla
    # para liberar la licencia.
    to_review = fields.Boolean(string='To Review', compute='_compute_to_review', search='_search_to_review')
    notes = fields.Text(string='Notes')

    # ==========================================
    # CÁLCULOS
    # ==========================================
    @api.depends('employee_id', 'department_id')
    @api.depends_context('pao_it_show_company')
    def _compute_responsible(self):
        for assignment in self:
            assignment.responsible = (assignment.employee_id.display_name
                                      or assignment.department_id.display_name or False)

    @api.depends('assignee_type', 'employee_id.department_id', 'department_id')
    def _compute_effective_department(self):
        for assignment in self:
            if assignment.assignee_type == 'employee':
                assignment.effective_department_id = assignment.employee_id.department_id
            else:
                assignment.effective_department_id = assignment.department_id

    @api.onchange('effective_department_id')
    def _onchange_effective_department(self):
        if self.assignee_type == 'department':
            self.department_id = self.effective_department_id

    @api.depends('subscription_id', 'responsible')
    def _compute_display_name(self):
        for assignment in self:
            assignment.display_name = f"{assignment.subscription_id.display_name} → {assignment.responsible or ''}"

    @api.depends('date_end')
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for assignment in self:
            assignment.state = 'closed' if assignment.date_end and assignment.date_end <= today else 'active'

    def _active_domain(self):
        today = fields.Date.context_today(self)
        return ['|', ('date_end', '=', False), ('date_end', '>', today)]

    def _search_state(self, operator, value):
        values = value if isinstance(value, (list, tuple)) else [value]
        if operator in ('!=', 'not in'):
            values = [v for v in ('active', 'closed') if v not in values]
        domains = []
        if 'active' in values:
            domains.append(self._active_domain())
        if 'closed' in values:
            domains.append([('date_end', '!=', False), ('date_end', '<=', fields.Date.context_today(self))])
        return expression.OR(domains) if domains else expression.FALSE_DOMAIN

    @api.depends('employee_id.active', 'date_end')
    def _compute_to_review(self):
        for assignment in self:
            employee = assignment.employee_id.with_context(active_test=False)
            assignment.to_review = bool(assignment.state == 'active' and employee and not employee.active)

    def _search_to_review(self, operator, value):
        archived = self.env['hr.employee'].with_context(active_test=False).search([('active', '=', False)])
        domain = expression.AND([[('employee_id', 'in', archived.ids)], self._active_domain()])
        positive = (operator == '=') == bool(value)
        return domain if positive else ['!'] + expression.normalize_domain(domain)

    # ==========================================
    # VALIDACIONES / INALTERABILIDAD
    # ==========================================
    @api.constrains('assignee_type', 'employee_id', 'department_id', 'date_start', 'date_end')
    def _check_assignment(self):
        for assignment in self:
            if assignment.assignee_type == 'employee' and (not assignment.employee_id or assignment.department_id):
                raise ValidationError(_("Please select the employee (and only the employee)."))
            if assignment.assignee_type == 'department' and (not assignment.department_id or assignment.employee_id):
                raise ValidationError(_("Please select the department (and only the department)."))
            if assignment.date_end and assignment.date_end < assignment.date_start:
                raise ValidationError(_("The end date of an assignment cannot be before its start date."))

    @api.onchange('assignee_type')
    def _onchange_assignee_type(self):
        if self.assignee_type == 'employee':
            self.department_id = False
        else:
            self.employee_id = False

    def write(self, vals):
        protected = set(vals) - EDITABLE_WHEN_CLOSED
        if protected and any(a._origin.state == 'closed' for a in self):
            raise UserError(_("A closed assignment cannot be modified (only its notes). "
                              "Register a new assignment instead."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        raise UserError(_("License assignments cannot be deleted: close them with an end date instead."))

    def action_close(self):
        today = fields.Date.context_today(self)
        for assignment in self.filtered(lambda a: a.state == 'active'):
            assignment.date_end = max(today, assignment.date_start)
        return True
