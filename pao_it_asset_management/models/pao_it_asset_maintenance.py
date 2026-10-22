from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Lo único que se puede modificar de un mantenimiento terminado (Done),
# además de la mensajería del chatter.
EDITABLE_WHEN_DONE = {'notes', 'attachment_ids'}


# ==========================================
# MANTENIMIENTO DE UN ACTIVO
# ==========================================
# Preventivo, correctivo o garantía. Modelo propio (NO el módulo nativo
# `maintenance`, que tiene su propio modelo de equipos). Si se marca "fuera
# de servicio", al iniciar/terminar genera los movimientos Send to Repair /
# Back from Repair a través del mismo asistente del entregable 2, para que
# las reglas de los movimientos no se dupliquen.
class PaoItAssetMaintenance(models.Model):
    _name = 'pao.it.asset.maintenance'
    _description = 'IT Asset Maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    asset_id = fields.Many2one('pao.it.asset', string='Asset', required=True, ondelete='cascade',
                               index=True, tracking=True)
    company_id = fields.Many2one(related='asset_id.company_id', store=True, index=True)
    category_id = fields.Many2one(related='asset_id.category_id', store=True, string='Category')
    maintenance_type = fields.Selection([
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('warranty', 'Warranty'),
    ], string='Type', required=True, default='corrective', tracking=True)
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', required=True, default='scheduled', readonly=True, tracking=True,
        group_expand='_group_expand_states')

    # --- FECHAS ---
    scheduled_date = fields.Date(string='Scheduled Date', required=True,
                                 default=fields.Date.context_today, tracking=True)
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_is_overdue',
                                search='_search_is_overdue')

    # --- QUIÉN ---
    technician_id = fields.Many2one('hr.employee', string='Technician', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Provider', tracking=True,
                                 help="External service provider or manufacturer (required for warranty).")

    # --- DETALLE ---
    issue_description = fields.Text(string='Issue Description')
    work_performed = fields.Text(string='Work Performed')
    rma_number = fields.Char(string='Warranty Case / RMA No.', tracking=True)
    condition_after_id = fields.Many2one('pao.it.condition', string='Condition After',
                                         ondelete='restrict')

    # --- COSTO ---
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    cost = fields.Monetary(string='Cost', currency_field='currency_id', tracking=True)
    account_move_id = fields.Many2one(
        'account.move', string='Vendor Bill / Journal Entry',
        domain="[('company_id', '=', company_id), ('move_type', 'in', ('in_invoice', 'in_refund', 'entry'))]")

    # --- FUERA DE SERVICIO ---
    take_out_of_service = fields.Boolean(
        string='Take Asset Out of Service',
        help="When started, the asset goes to In Repair (Send to Repair movement); "
             "when done or cancelled, it goes back to its previous status (Back from Repair).")
    repair_movement_id = fields.Many2one('pao.it.asset.movement', string='Send to Repair Movement',
                                         readonly=True, copy=False)

    # --- ENVÍO (p. ej. equipo mandado al proveedor por garantía) ---
    requires_shipping = fields.Boolean(string='Requires Shipping')
    carrier_id = fields.Many2one('pao.it.carrier', string='Carrier', ondelete='restrict')
    tracking_number = fields.Char(string='Tracking Number')
    ship_date = fields.Date(string='Ship Date')
    estimated_delivery_date = fields.Date(string='Estimated Delivery Date')
    actual_delivery_date = fields.Date(string='Actual Delivery Date')
    shipping_currency_id = fields.Many2one('res.currency', string='Shipping Currency',
                                           default=lambda self: self.env.company.currency_id)
    shipping_cost = fields.Monetary(string='Shipping Cost', currency_field='shipping_currency_id')
    shipping_move_id = fields.Many2one(
        'account.move', string='Shipping Bill / Journal Entry',
        domain="[('company_id', '=', company_id), ('move_type', 'in', ('in_invoice', 'in_refund', 'entry'))]")

    # --- EDITABLES SIEMPRE ---
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', 'pao_it_asset_maintenance_attachment_rel',
                                      'maintenance_id', 'attachment_id', string='Attachments')

    # ==========================================
    # CÁLCULOS
    # ==========================================
    @api.model
    def _group_expand_states(self, states, domain, order):
        return [key for key, _label in self._fields['state'].selection]

    @api.depends('state', 'scheduled_date')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for maintenance in self:
            maintenance.is_overdue = (maintenance.state == 'scheduled'
                                      and maintenance.scheduled_date
                                      and maintenance.scheduled_date < today)

    def _search_is_overdue(self, operator, value):
        today = fields.Date.context_today(self)
        domain = [('state', '=', 'scheduled'), ('scheduled_date', '<', today)]
        positive = (operator == '=') == bool(value)
        return domain if positive else ['!', '&'] + domain

    # ==========================================
    # CREATE / WRITE / UNLINK
    # ==========================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('pao.it.asset.maintenance') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        # Terminado = inalterable, salvo notas, adjuntos y el chatter.
        protected = {key for key in vals
                     if key not in EDITABLE_WHEN_DONE and not key.startswith(('message_', 'activity_'))}
        if protected and self.filtered(lambda m: m.state == 'done') and not self.env.context.get('pao_it_maintenance_system'):
            raise UserError(_("A finished maintenance cannot be modified. Only notes and attachments can be updated."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_pending(self):
        for maintenance in self:
            if maintenance.state not in ('scheduled', 'cancelled'):
                raise UserError(_(
                    "Maintenance %s cannot be deleted: only scheduled or cancelled maintenances can be deleted.",
                    maintenance.name))

    # ==========================================
    # FLUJO
    # ==========================================
    def _run_movement(self, movement_type, date, condition=False, reason=False):
        """Registra un movimiento del activo con el asistente del entregable 2
        (mismas validaciones) y lo liga a este mantenimiento."""
        self.ensure_one()
        wizard = self.env['pao.it.asset.movement.wizard'].create({
            'movement_type': movement_type,
            'asset_ids': [(6, 0, self.asset_id.ids)],
            'date': date,
            'condition_id': condition and condition.id,
            'reason': reason or self.issue_description or self.name,
            'maintenance_id': self.id,
        })
        wizard.action_confirm()
        return self.asset_id._get_last_movement((movement_type,))

    def action_start(self):
        today = fields.Date.context_today(self)
        for maintenance in self:
            if maintenance.state != 'scheduled':
                raise UserError(_("Only scheduled maintenances can be started."))
            maintenance._check_provider()
            start_date = maintenance.start_date or today
            vals = {'state': 'in_progress', 'start_date': start_date}
            if maintenance.take_out_of_service and maintenance.asset_id.state != 'in_repair':
                movement = maintenance._run_movement('send_to_repair', start_date)
                vals['repair_movement_id'] = movement.id
            maintenance.write(vals)
        return True

    def action_done(self):
        """Abre una ventana que pide fecha de fin, condición final y trabajo
        realizado. Así se puede terminar desde cualquier lugar (incluida la
        pestaña de solo lectura del activo), sin depender de que el
        formulario sea editable."""
        self.ensure_one()
        if self.state not in ('scheduled', 'in_progress'):
            raise UserError(_("Only scheduled or in-progress maintenances can be finished."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mark as Done'),
            'res_model': 'pao.it.asset.maintenance.done.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_maintenance_id': self.id,
                'default_condition_after_id': (self.condition_after_id or self.asset_id.condition_id).id,
                'default_work_performed': self.work_performed,
            },
        }

    def _finish(self, end_date, condition, work_performed=False):
        """Termina el mantenimiento (desde la ventana de action_done). Si
        estaba solo programado, primero se inicia (mismo día que el fin, si
        no tenía fecha de inicio)."""
        self.ensure_one()
        if not condition:
            raise UserError(_("Please indicate the condition of the asset after the maintenance."))
        if self.state == 'scheduled':
            if not self.start_date:
                self.start_date = end_date
            self.action_start()
        if self.state != 'in_progress':
            raise UserError(_("Only maintenances in progress can be finished."))
        if end_date < self.start_date:
            raise UserError(_("The end date cannot be before the start date."))
        self._back_to_service(end_date, condition)
        vals = {'state': 'done', 'end_date': end_date, 'condition_after_id': condition.id}
        if work_performed:
            vals['work_performed'] = work_performed
        self.write(vals)
        if self.maintenance_type == 'preventive':
            self.asset_id._plan_next_preventive()
        return True

    def action_cancel(self):
        today = fields.Date.context_today(self)
        for maintenance in self:
            if maintenance.state not in ('scheduled', 'in_progress'):
                raise UserError(_("Only scheduled or in-progress maintenances can be cancelled."))
            if maintenance.state == 'in_progress':
                # Que el activo no se quede atorado en In Repair.
                maintenance._back_to_service(today, False,
                                             reason=_("Maintenance %s cancelled.", maintenance.name))
            maintenance.write({'state': 'cancelled'})
            if maintenance.maintenance_type == 'preventive':
                # Cancelar "salta" ese ciclo: se programa el siguiente
                # (no aplica si el activo ya no está Available/Assigned).
                maintenance.asset_id._plan_next_preventive()
        return True

    def _back_to_service(self, date, condition, reason=False):
        """Back from Repair si ESTE mantenimiento sacó al activo de servicio y
        sigue en reparación; si no, solo actualiza la condición."""
        self.ensure_one()
        if self.repair_movement_id and self.asset_id.state == 'in_repair':
            self._run_movement('back_from_repair', date, condition=condition, reason=reason)
        elif condition:
            self.asset_id.condition_id = condition

    def _check_provider(self):
        for maintenance in self:
            if maintenance.maintenance_type == 'warranty' and not maintenance.partner_id:
                raise UserError(_("Please indicate the provider of the warranty service."))

    @api.constrains('maintenance_type', 'partner_id', 'state')
    def _check_warranty_provider(self):
        self.filtered(lambda m: m.state in ('in_progress', 'done'))._check_provider()
