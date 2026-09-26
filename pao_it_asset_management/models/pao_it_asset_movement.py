from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .pao_it_asset import ASSET_STATES

MOVEMENT_TYPES = [
    ('register', 'Register'),
    ('assign', 'Assign'),
    ('reassign', 'Reassign'),
    ('relocate', 'Relocate'),
    ('confirm_delivery', 'Confirm Delivery'),
    ('cancel_shipment', 'Cancel Shipment'),
    ('return', 'Return'),
    ('send_to_repair', 'Send to Repair'),
    ('back_from_repair', 'Back from Repair'),
    ('retire', 'Retire'),
    ('report_lost', 'Report Lost / Stolen'),
    ('recover', 'Recover'),
]

# Lo único que se puede modificar de un movimiento ya registrado.
EDITABLE_FIELDS = {'notes', 'attachment_ids'}


# ==========================================
# HISTORIAL DE MOVIMIENTOS DEL ACTIVO
# ==========================================
# Un renglón por cada cambio de estatus / responsable / compañía / ubicación
# del activo, con la foto de "antes" y "después". Es INALTERABLE: nadie (ni
# un administrador) puede editarlo ni borrarlo, excepto sus notas y
# adjuntos. Un error se corrige con un movimiento nuevo. Los renglones los
# crea únicamente el asistente (pao_it_asset_movement_wizard.py) y el alta
# del activo (Register).
class PaoItAssetMovement(models.Model):
    _name = 'pao.it.asset.movement'
    _description = 'IT Asset Movement'
    _order = 'date desc, id desc'
    _rec_name = 'movement_type'

    asset_id = fields.Many2one('pao.it.asset', string='Asset', required=True, ondelete='cascade',
                               index=True, readonly=True)
    # Compañía ACTUAL del activo: la regla multi-compañía muestra el
    # historial completo a quien puede ver el activo hoy.
    company_id = fields.Many2one(related='asset_id.company_id', store=True, index=True)
    movement_type = fields.Selection(MOVEMENT_TYPES, string='Movement', required=True, readonly=True)
    date = fields.Date(string='Date', required=True, readonly=True, index=True,
                       help="Effective date of the movement.")
    # Periodo: desde `date` hasta el siguiente movimiento del mismo activo.
    date_end = fields.Date(string='Until', compute='_compute_date_end', store=True,
                           help="Date of the next movement of this asset. Empty while this is the current one.")
    user_id = fields.Many2one('res.users', string='Performed By', required=True, readonly=True,
                              default=lambda self: self.env.user)

    # --- ANTES → DESPUÉS ---
    state_from = fields.Selection(ASSET_STATES, string='Status (Before)', readonly=True)
    state_to = fields.Selection(ASSET_STATES, string='Status', readonly=True)
    employee_from_id = fields.Many2one('hr.employee', string='Employee (Before)', readonly=True,
                                       ondelete='restrict')
    employee_to_id = fields.Many2one('hr.employee', string='Employee', readonly=True,
                                     ondelete='restrict', index=True)
    department_from_id = fields.Many2one('hr.department', string='Department (Before)', readonly=True,
                                         ondelete='restrict')
    department_to_id = fields.Many2one('hr.department', string='Department', readonly=True,
                                       ondelete='restrict')
    company_from_id = fields.Many2one('res.company', string='Company (Before)', readonly=True)
    company_to_id = fields.Many2one('res.company', string='Company (After)', readonly=True)
    location_from_id = fields.Many2one('pao.it.location', string='Location (Before)', readonly=True,
                                       ondelete='restrict')
    location_to_id = fields.Many2one('pao.it.location', string='Location', readonly=True,
                                     ondelete='restrict')
    condition_from_id = fields.Many2one('pao.it.condition', string='Condition (Before)', readonly=True,
                                        ondelete='restrict')
    condition_to_id = fields.Many2one('pao.it.condition', string='Condition', readonly=True,
                                      ondelete='restrict')
    responsible_from = fields.Char(string='Responsible (Before)', compute='_compute_responsible')
    responsible_to = fields.Char(string='Responsible', compute='_compute_responsible')
    company_changed = fields.Boolean(string='Company Changed', compute='_compute_company_changed',
                                     store=True)

    # --- MOTIVO ---
    reason = fields.Text(string='Reason', readonly=True)
    retirement_reason_id = fields.Many2one('pao.it.retirement.reason', string='Retirement Reason',
                                           readonly=True, ondelete='restrict')

    # --- ENVÍO (Assign/Reassign con envío) ---
    requires_shipping = fields.Boolean(string='Requires Shipping', readonly=True)
    carrier_id = fields.Many2one('pao.it.carrier', string='Carrier', readonly=True, ondelete='restrict')
    tracking_number = fields.Char(string='Tracking Number', readonly=True)
    ship_date = fields.Date(string='Ship Date', readonly=True)
    estimated_delivery_date = fields.Date(string='Estimated Delivery Date', readonly=True)
    shipping_currency_id = fields.Many2one('res.currency', string='Shipping Currency', readonly=True)
    shipping_cost = fields.Monetary(string='Shipping Cost', currency_field='shipping_currency_id',
                                    readonly=True)
    shipping_move_id = fields.Many2one('account.move', string='Shipping Bill / Journal Entry',
                                       readonly=True)
    # En Confirm Delivery / Cancel Shipment: el envío al que se refiere.
    shipment_movement_id = fields.Many2one('pao.it.asset.movement', string='Shipment', readonly=True)
    actual_delivery_date = fields.Date(string='Actual Delivery Date', readonly=True)

    # --- EDITABLES ---
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', 'pao_it_asset_movement_attachment_rel',
                                      'movement_id', 'attachment_id', string='Attachments')

    # ==========================================
    # CÁLCULOS
    # ==========================================
    @api.depends('asset_id.movement_ids.date')
    def _compute_date_end(self):
        for movement in self:
            siblings = movement.asset_id.movement_ids.sorted(lambda m: (m.date, m._origin.id or 0))
            ids = [m._origin.id or 0 for m in siblings]
            key = movement._origin.id or 0
            index = ids.index(key) if key in ids else -1
            following = siblings[index + 1:index + 2] if index >= 0 else siblings.browse()
            movement.date_end = following.date if following else False

    @api.depends('employee_from_id', 'employee_to_id', 'department_from_id', 'department_to_id')
    def _compute_responsible(self):
        for movement in self:
            movement.responsible_from = (movement.employee_from_id.name
                                         or movement.department_from_id.display_name or False)
            movement.responsible_to = (movement.employee_to_id.name
                                       or movement.department_to_id.display_name or False)

    @api.depends('company_from_id', 'company_to_id')
    def _compute_company_changed(self):
        for movement in self:
            movement.company_changed = bool(movement.company_from_id
                                            and movement.company_from_id != movement.company_to_id)

    @api.depends('movement_type', 'date')
    def _compute_display_name(self):
        labels = dict(self._fields['movement_type']._description_selection(self.env))
        for movement in self:
            movement.display_name = f"{labels.get(movement.movement_type)} ({movement.date or ''})"

    # ==========================================
    # INALTERABILIDAD
    # ==========================================
    def write(self, vals):
        forbidden = set(vals) - EDITABLE_FIELDS
        if forbidden:
            raise UserError(_(
                "Asset movements cannot be modified. Only notes and attachments can be updated; "
                "any correction must be registered as a new movement."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        raise UserError(_("Asset movements cannot be deleted."))
