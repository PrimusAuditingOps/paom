from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from .pao_it_asset_movement import MOVEMENT_TYPES

# Desde qué estatus se permite cada movimiento (Register no pasa por aquí).
ALLOWED_FROM = {
    'assign': ('available',),
    'reassign': ('assigned',),
    'relocate': ('available', 'assigned', 'in_repair'),
    'confirm_delivery': ('in_transit',),
    'cancel_shipment': ('in_transit',),
    'return': ('assigned',),
    'send_to_repair': ('available', 'assigned'),
    'back_from_repair': ('in_repair',),
    'retire': ('available', 'assigned', 'in_repair'),
    'report_lost': ('available', 'assigned', 'in_transit', 'in_repair'),
    'recover': ('lost',),
}
# Movimientos que se pueden aplicar a varios activos a la vez.
MULTI_ASSET_TYPES = ('assign', 'return')
# Movimientos que piden motivo obligatorio.
REASON_REQUIRED_TYPES = ('cancel_shipment', 'send_to_repair', 'report_lost')


# ==========================================
# ASISTENTE DE MOVIMIENTOS
# ==========================================
# Una sola ventana para todas las acciones: muestra los campos que aplican
# según `movement_type`, valida las reglas, crea el renglón del historial y
# actualiza el activo. Solo lo usan los administradores.
class PaoItAssetMovementWizard(models.TransientModel):
    _name = 'pao.it.asset.movement.wizard'
    _description = 'IT Asset Movement Wizard'

    movement_type = fields.Selection(
        [m for m in MOVEMENT_TYPES if m[0] != 'register'], string='Movement', required=True)
    asset_ids = fields.Many2many('pao.it.asset', string='Assets', required=True)
    asset_count = fields.Integer(compute='_compute_asset_count')
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today,
                       help="Effective date of the movement. It can be in the past, never in the future.")

    # --- NUEVO RESPONSABLE (Assign / Reassign) ---
    assignee_type = fields.Selection([
        ('employee', 'Employee'),
        ('department', 'Department'),
    ], string='Assign To', default='employee')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    # Compañía destino: la del responsable (Assign/Reassign); elegible solo
    # al reubicar un activo Available. En los demás casos no cambia.
    company_id = fields.Many2one('res.company', string='Company',
                                 compute='_compute_company_id', store=True, readonly=False)
    can_change_company = fields.Boolean(compute='_compute_can_change_company')
    location_id = fields.Many2one('pao.it.location', string='Location',
                                  domain="[('company_id', '=', company_id)]")
    condition_id = fields.Many2one('pao.it.condition', string='Condition')

    # --- MOTIVO ---
    reason = fields.Text(string='Reason')
    retirement_reason_id = fields.Many2one('pao.it.retirement.reason', string='Retirement Reason')

    # --- ENVÍO ---
    requires_shipping = fields.Boolean(string='Requires Shipping')
    carrier_id = fields.Many2one('pao.it.carrier', string='Carrier')
    tracking_number = fields.Char(string='Tracking Number')
    ship_date = fields.Date(string='Ship Date', default=fields.Date.context_today)
    estimated_delivery_date = fields.Date(string='Estimated Delivery Date')
    shipping_currency_id = fields.Many2one('res.currency', string='Shipping Currency',
                                           default=lambda self: self.env.company.currency_id)
    shipping_cost = fields.Monetary(string='Shipping Cost', currency_field='shipping_currency_id')
    shipping_move_id = fields.Many2one('account.move', string='Shipping Bill / Journal Entry',
                                       domain="[('move_type', 'in', ('in_invoice', 'in_refund', 'entry'))]")

    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', 'pao_it_asset_movement_wizard_attachment_rel',
                                      'wizard_id', 'attachment_id', string='Attachments')

    # Aviso (no bloquea): el activo tiene distribución analítica y cambia de
    # departamento.
    analytic_warning = fields.Char(compute='_compute_analytic_warning')

    # ==========================================
    # CÁLCULOS
    # ==========================================
    @api.depends('asset_ids')
    def _compute_asset_count(self):
        for wizard in self:
            wizard.asset_count = len(wizard.asset_ids)

    @api.depends('movement_type', 'assignee_type', 'employee_id', 'department_id', 'asset_ids')
    def _compute_company_id(self):
        for wizard in self:
            current = wizard.asset_ids[:1].company_id
            if wizard.movement_type in ('assign', 'reassign'):
                if wizard.assignee_type == 'employee' and wizard.employee_id:
                    wizard.company_id = wizard.employee_id.company_id or current
                elif wizard.assignee_type == 'department' and wizard.department_id:
                    wizard.company_id = wizard.department_id.company_id or current
                else:
                    wizard.company_id = current
            elif not wizard.company_id:
                wizard.company_id = current

    @api.depends('movement_type', 'asset_ids.state')
    def _compute_can_change_company(self):
        for wizard in self:
            wizard.can_change_company = (wizard.movement_type == 'relocate'
                                         and len(wizard.asset_ids) == 1
                                         and wizard.asset_ids.state == 'available')

    @api.depends('movement_type', 'assignee_type', 'employee_id', 'department_id', 'asset_ids')
    def _compute_analytic_warning(self):
        for wizard in self:
            warning = False
            if wizard.movement_type in ('assign', 'reassign'):
                new_department = (wizard.employee_id.department_id if wizard.assignee_type == 'employee'
                                  else wizard.department_id)
                affected = wizard.asset_ids.filtered(
                    lambda a: a.analytic_distribution and a.department_id != new_department)
                if new_department and affected:
                    warning = _("Review the analytic distribution of: %s. "
                                "The asset is changing department.",
                                ', '.join(affected.mapped('asset_tag')))
            wizard.analytic_warning = warning

    # ==========================================
    # ONCHANGES
    # ==========================================
    @api.onchange('assignee_type')
    def _onchange_assignee_type(self):
        if self.assignee_type == 'employee':
            self.department_id = False
        else:
            self.employee_id = False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.location_id and self.location_id.company_id != self.company_id:
            self.location_id = False

    # ==========================================
    # VALIDACIÓN Y APLICACIÓN
    # ==========================================
    def _check_common(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        labels = dict(self._fields['movement_type']._description_selection(self.env))
        state_labels = dict(self.env['pao.it.asset']._fields['state']._description_selection(self.env))
        if len(self.asset_ids) > 1 and self.movement_type not in MULTI_ASSET_TYPES:
            raise UserError(_("The movement %s can only be applied to one asset at a time.",
                              labels[self.movement_type]))
        if self.date > today:
            raise ValidationError(_("The movement date cannot be in the future."))
        for asset in self.asset_ids:
            if asset.state not in ALLOWED_FROM[self.movement_type]:
                raise UserError(_(
                    "The movement %(movement)s is not allowed for asset %(tag)s in status %(state)s.",
                    movement=labels[self.movement_type], tag=asset.asset_tag,
                    state=state_labels.get(asset.state)))
            if self.date < asset.registration_date:
                raise ValidationError(_(
                    "The movement date cannot be before the registration date of asset %(tag)s (%(date)s).",
                    tag=asset.asset_tag, date=asset.registration_date))
            last = asset._get_last_movement()
            if last and self.date < last.date:
                raise ValidationError(_(
                    "The movement date cannot be before the last movement of asset %(tag)s (%(date)s).",
                    tag=asset.asset_tag, date=last.date))
        if self.movement_type in REASON_REQUIRED_TYPES and not (self.reason or '').strip():
            raise UserError(_("Please indicate the reason for this movement."))
        if self.movement_type == 'retire' and not self.retirement_reason_id:
            raise UserError(_("Please select the retirement reason."))
        if self.movement_type in ('assign', 'reassign'):
            if self.assignee_type == 'employee' and not self.employee_id:
                raise UserError(_("Please select the employee."))
            if self.assignee_type == 'department' and not self.department_id:
                raise UserError(_("Please select the department."))
        if self.movement_type == 'relocate' and not self.location_id:
            raise UserError(_("Please select the new location."))
        if self.location_id and self.company_id and self.location_id.company_id != self.company_id:
            raise ValidationError(_("The location %(location)s belongs to another company.",
                                    location=self.location_id.display_name))

    def _snapshot(self, asset):
        return {
            'state': asset.state,
            'employee': asset.employee_id,
            'department': asset.assigned_department_id,
            'company': asset.company_id,
            'location': asset.location_id,
            'condition': asset.condition_id,
        }

    def _compute_after(self, asset, before):
        """Devuelve (after, extra_movement_vals) para un activo."""
        after = dict(before)
        extra = {}
        mtype = self.movement_type
        Employee = self.env['hr.employee']
        Department = self.env['hr.department']
        if self.condition_id:
            after['condition'] = self.condition_id

        if mtype in ('assign', 'reassign'):
            employee = self.employee_id if self.assignee_type == 'employee' else Employee
            department = self.department_id if self.assignee_type == 'department' else Department
            if mtype == 'reassign' and employee == before['employee'] and department == before['department']:
                raise UserError(_("Asset %s is already assigned to that responsible.", asset.asset_tag))
            company = self.company_id or before['company']
            after.update({
                'employee': employee,
                'department': department,
                'company': company,
                'location': self.location_id or (before['location'] if company == before['company']
                                                 else self.env['pao.it.location']),
                'state': 'in_transit' if self.requires_shipping else 'assigned',
            })
            if self.requires_shipping:
                extra.update({
                    'requires_shipping': True,
                    'carrier_id': self.carrier_id.id,
                    'tracking_number': self.tracking_number,
                    'ship_date': self.ship_date,
                    'estimated_delivery_date': self.estimated_delivery_date,
                    'shipping_currency_id': self.shipping_currency_id.id,
                    'shipping_cost': self.shipping_cost,
                    'shipping_move_id': self.shipping_move_id.id,
                })

        elif mtype == 'relocate':
            company = self.company_id if self.can_change_company else before['company']
            if self.location_id.company_id != company:
                raise ValidationError(_("The location %(location)s belongs to another company.",
                                        location=self.location_id.display_name))
            after.update({'company': company, 'location': self.location_id})

        elif mtype in ('confirm_delivery', 'cancel_shipment'):
            shipment = asset._get_last_movement(('assign', 'reassign')).filtered('requires_shipping')
            if not shipment:
                raise UserError(_("No shipment was found for asset %s.", asset.asset_tag))
            extra['shipment_movement_id'] = shipment.id
            if mtype == 'confirm_delivery':
                after['state'] = 'assigned'
                extra['actual_delivery_date'] = self.date
            else:
                # Deshace el envío: el activo vuelve exactamente a como estaba
                # antes de mandarlo (el "antes" del renglón del envío).
                after.update({
                    'state': shipment.state_from,
                    'employee': shipment.employee_from_id,
                    'department': shipment.department_from_id,
                    'company': shipment.company_from_id,
                    'location': shipment.location_from_id,
                })

        elif mtype == 'return':
            after.update({
                'state': 'available',
                'employee': Employee,
                'department': Department,
                'location': self.location_id or before['location'],
            })

        elif mtype == 'send_to_repair':
            after['state'] = 'in_repair'

        elif mtype == 'back_from_repair':
            repair = asset._get_last_movement(('send_to_repair',))
            after['state'] = repair.state_from or 'available'

        elif mtype == 'retire':
            after.update({'state': 'retired', 'employee': Employee, 'department': Department})
            extra['retirement_reason_id'] = self.retirement_reason_id.id

        elif mtype == 'report_lost':
            # Conserva al responsable: el activo sigue mostrando quién lo tenía.
            after['state'] = 'lost'

        elif mtype == 'recover':
            after.update({
                'state': 'available',
                'employee': Employee,
                'department': Department,
                'location': self.location_id or before['location'],
            })
        return after, extra

    def action_confirm(self):
        self.ensure_one()
        self._check_common()
        Movement = self.env['pao.it.asset.movement']
        movements = Movement
        for asset in self.asset_ids:
            before = self._snapshot(asset)
            after, extra = self._compute_after(asset, before)
            movement_vals = {
                'asset_id': asset.id,
                'movement_type': self.movement_type,
                'date': self.date,
                'state_from': before['state'],
                'state_to': after['state'],
                'employee_from_id': before['employee'].id,
                'employee_to_id': after['employee'].id,
                'department_from_id': before['department'].id,
                'department_to_id': after['department'].id,
                'company_from_id': before['company'].id,
                'company_to_id': after['company'].id,
                'location_from_id': before['location'].id,
                'location_to_id': after['location'].id,
                'condition_from_id': before['condition'].id,
                'condition_to_id': after['condition'].id,
                'reason': self.reason,
                'notes': self.notes,
                **extra,
            }
            movement = Movement.create(movement_vals)
            if self.attachment_ids:
                # Cada movimiento recibe su propia copia de los adjuntos.
                movement.attachment_ids = [
                    (4, att.copy({'res_model': movement._name, 'res_id': movement.id}).id)
                    for att in self.attachment_ids
                ]
            movements |= movement
            asset.write({
                'state': after['state'],
                'employee_id': after['employee'].id,
                'assigned_department_id': after['department'].id,
                'company_id': after['company'].id,
                'location_id': after['location'].id,
                'condition_id': after['condition'].id,
            })
        return {'type': 'ir.actions.act_window_close'}
