import re
from collections import defaultdict
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_compare

# Días antes del fin de garantía en que el activo se considera "por vencer".
WARRANTY_EXPIRING_DAYS = 30

# Estatus del activo. Fijos en código: las reglas de los movimientos
# (pao_it_asset_movement.py) dependen de ellos. Los reutiliza el historial.
ASSET_STATES = [
    ('available', 'Available'),
    ('assigned', 'Assigned'),
    ('in_transit', 'In Transit'),
    ('in_repair', 'In Repair'),
    ('retired', 'Retired'),
    ('lost', 'Lost / Stolen'),
]


# ==========================================
# ACTIVO DE HARDWARE
# ==========================================
class PaoItAsset(models.Model):
    _name = 'pao.it.asset'
    _description = 'IT Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin', 'analytic.mixin']
    _rec_name = 'asset_tag'
    _order = 'asset_tag'

    # --- IDENTIFICACIÓN ---
    # Lo captura el administrador; se normaliza a mayúsculas y sin espacios
    # (ver _normalize_asset_tag) para que "lpt-mx-076" y "LPT-MX-076" no
    # puedan coexistir como activos distintos.
    asset_tag = fields.Char(string='Asset Tag', required=True, copy=False, tracking=True, index=True)
    category_id = fields.Many2one('pao.it.asset.category', string='Category', required=True,
                                  ondelete='restrict', tracking=True)
    requires_imei = fields.Boolean(related='category_id.requires_imei')
    brand_id = fields.Many2one('pao.it.brand', string='Brand', ondelete='restrict', tracking=True)
    model_id = fields.Many2one('pao.it.model', string='Model', ondelete='restrict', tracking=True,
                               domain="[('brand_id', '=?', brand_id)]")
    condition_id = fields.Many2one('pao.it.condition', string='Condition', ondelete='restrict',
                                   tracking=True)

    # --- ESTATUS ---
    # Solo lectura en la ficha: lo cambian únicamente los movimientos
    # (asignar, enviar, devolver, dar de baja...).
    state = fields.Selection(ASSET_STATES, string='Status', required=True, default='available',
                             readonly=True, tracking=True, group_expand='_group_expand_states')

    # --- COMPAÑÍA Y UBICACIÓN ---
    # company_id = compañía donde el activo está EN USO (no hay "compañía
    # dueña"). Obligatoria: no existen activos globales. Compañía y ubicación
    # solo se capturan al crear el activo; después cambian únicamente con
    # movimientos (la vista las bloquea una vez guardado el registro).
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True,
                                 default=lambda self: self.env.company, tracking=True)
    location_id = fields.Many2one('pao.it.location', string='Location', ondelete='restrict',
                                  tracking=True, domain="[('company_id', '=', company_id)]")
    location_type = fields.Selection(related='location_id.location_type', store=True)

    # --- ALTA E HISTORIAL ---
    # Fecha del movimiento "Register". Ningún movimiento puede ser anterior a
    # ella; en la carga inicial se captura la fecha real de alta/compra.
    registration_date = fields.Date(string='Registration Date', required=True,
                                    default=fields.Date.context_today)
    movement_ids = fields.One2many('pao.it.asset.movement', 'asset_id', string='History')

    # --- RESPONSABLE ---
    # Empleado O departamento (nunca ambos). Solo lectura: los llenan los
    # movimientos. department_id es el departamento efectivo (el del
    # empleado, o el asignado directamente) y existe para filtrar y agrupar.
    # Un activo Lost/Stolen CONSERVA a su último responsable.
    employee_id = fields.Many2one('hr.employee', string='Assigned Employee', readonly=True,
                                  tracking=True, index=True)
    assigned_department_id = fields.Many2one('hr.department', string='Assigned Department',
                                             readonly=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department',
                                    compute='_compute_department_id', store=True)

    # --- DETALLES ---
    serial_number = fields.Char(string='Serial Number', tracking=True, index=True)
    product_number = fields.Char(string='Product Number')
    imei = fields.Char(string='IMEI', tracking=True, index=True)
    specifications = fields.Text(string='Specifications')
    notes = fields.Text(string='Notes')

    # --- COMPRA ---
    # Registro manual: la PO es opcional y NUNCA crea el activo. Si se elige
    # PO + línea, se prellenan fecha, costo (unitario sin impuestos) y
    # moneda, que siguen siendo editables. Sin PO, se usa un "otro método de
    # compra" (catálogo) y texto libre de cómo se pagó; la captura libre
    # jamás crea proveedores.
    purchase_source = fields.Selection([
        ('purchase_order', 'Purchase Order'),
        ('other', 'Other Purchase Method'),
    ], string='Purchase Source', tracking=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order', tracking=True,
        domain="[('company_id', '=', company_id), ('state', 'in', ('purchase', 'done'))]")
    purchase_line_id = fields.Many2one(
        'purchase.order.line', string='Purchase Order Line',
        domain="[('order_id', '=', purchase_order_id), ('display_type', '=', False)]")
    # Copias de solo lectura para quien no tiene acceso a Compras/Contabilidad
    # (la vista las muestra en lugar del campo relacional). Guardadas, para
    # que buscar por PO no requiera permisos sobre purchase.order.
    purchase_order_ref = fields.Char(related='purchase_order_id.name', string='Purchase Order Ref.',
                                     store=True)
    vendor_id = fields.Many2one(related='purchase_order_id.partner_id', string='Vendor', store=True)
    purchase_method_id = fields.Many2one('pao.it.purchase.method', string='Other Purchase Method',
                                         ondelete='restrict', tracking=True)
    payment_details = fields.Char(string='Payment Details',
                                  help="How it was paid, e.g. corporate card, reimbursement.")
    purchase_date = fields.Date(string='Purchase Date', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    purchase_cost = fields.Monetary(string='Purchase Cost', currency_field='currency_id',
                                    tracking=True)
    # Facturas de la PO: se toman SOLAS de la línea de la PO elegida (todas,
    # en borrador o publicadas, no canceladas). No se guardan: si la factura
    # se crea después que el activo, aparece sin tener que editarlo.
    # compute_sudo: el resumen de texto (purchase_move_summary) debe poder
    # verlo también quien no tiene acceso a Compras/Contabilidad.
    purchase_move_ids = fields.Many2many('account.move', string='Vendor Bills',
                                         compute='_compute_purchase_moves', compute_sudo=True)
    purchase_move_summary = fields.Char(string='Vendor Bills Summary',
                                        compute='_compute_purchase_moves', compute_sudo=True)
    # Solo para origen "Other Purchase Method": liga MANUAL a la factura de
    # proveedor O póliza (compras con tarjeta que se solventan con pólizas
    # de ajuste). Opcional y capturable después.
    account_move_id = fields.Many2one(
        'account.move', string='Vendor Bill / Journal Entry',
        domain="[('company_id', '=', company_id), ('move_type', 'in', ('in_invoice', 'in_refund', 'entry'))]")
    account_move_ref = fields.Char(related='account_move_id.name', string='Vendor Bill / Journal Entry Ref.',
                                   store=True)

    # --- GARANTÍA ---
    warranty_start = fields.Date(string='Warranty Start')
    warranty_end = fields.Date(string='Warranty End', tracking=True)
    warranty_partner_id = fields.Many2one('res.partner', string='Warranty Provider')
    warranty_notes = fields.Text(string='Warranty Coverage / Notes')
    warranty_status = fields.Selection([
        ('none', 'No Warranty'),
        ('active', 'Under Warranty'),
        ('expiring', 'Warranty Expiring'),
        ('expired', 'Warranty Expired'),
    ], string='Warranty Status', compute='_compute_warranty_status', search='_search_warranty_status')

    # --- GALERÍA ---
    image_ids = fields.One2many('pao.it.asset.image', 'asset_id', string='Gallery')

    _sql_constraints = [
        ('asset_tag_uniq', 'unique(asset_tag)', 'The Asset Tag must be unique.'),
    ]

    # ==========================================
    # CÁLCULOS
    # ==========================================
    @api.model
    def _group_expand_states(self, states, domain, order):
        return [key for key, _label in self._fields['state'].selection]

    @api.depends('employee_id.department_id', 'assigned_department_id')
    def _compute_department_id(self):
        for asset in self:
            asset.department_id = asset.employee_id.department_id or asset.assigned_department_id

    @api.depends('purchase_source', 'purchase_line_id.invoice_lines.move_id.state')
    def _compute_purchase_moves(self):
        state_labels = dict(self.env['account.move']._fields['state']._description_selection(self.env))
        for asset in self:
            moves = self.env['account.move']
            if asset.purchase_source == 'purchase_order' and asset.purchase_line_id:
                moves = asset.purchase_line_id.invoice_lines.move_id.filtered(
                    lambda m: m.move_type in ('in_invoice', 'in_refund') and m.state in ('draft', 'posted'))
            asset.purchase_move_ids = moves
            asset.purchase_move_summary = ', '.join(
                f"{move.name or '/'} ({state_labels.get(move.state)})" for move in moves)

    @api.depends('warranty_end')
    def _compute_warranty_status(self):
        today = fields.Date.context_today(self)
        for asset in self:
            asset.warranty_status = asset._get_warranty_status(today)

    def _get_warranty_status(self, today):
        self.ensure_one()
        if not self.warranty_end:
            return 'none'
        if self.warranty_end < today:
            return 'expired'
        if self.warranty_end <= today + timedelta(days=WARRANTY_EXPIRING_DAYS):
            return 'expiring'
        return 'active'

    def _search_warranty_status(self, operator, value):
        today = fields.Date.context_today(self)
        limit = today + timedelta(days=WARRANTY_EXPIRING_DAYS)
        domains = {
            'none': [('warranty_end', '=', False)],
            'expired': [('warranty_end', '<', today)],
            'expiring': [('warranty_end', '>=', today), ('warranty_end', '<=', limit)],
            'active': [('warranty_end', '>', limit)],
        }
        if operator not in ('=', 'in', '!=', 'not in'):
            raise ValidationError(_("Unsupported search on warranty status."))
        values = set(value if isinstance(value, (list, tuple)) else [value])
        # La negación se resuelve como "cualquiera de los demás estados": los
        # cuatro dominios cubren todos los casos sin traslaparse.
        if operator in ('!=', 'not in'):
            values = set(domains) - values
        return expression.OR([domains[val] for val in values if val in domains]) or expression.FALSE_DOMAIN

    # ==========================================
    # ONCHANGES (prellenado desde la compra)
    # ==========================================
    @api.onchange('brand_id')
    def _onchange_brand_id(self):
        if self.model_id and self.model_id.brand_id != self.brand_id:
            self.model_id = False

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id and not self.brand_id:
            self.brand_id = self.model_id.brand_id

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.location_id and self.location_id.company_id != self.company_id:
            self.location_id = False
        if self.purchase_order_id and self.purchase_order_id.company_id != self.company_id:
            self.purchase_order_id = False

    @api.onchange('purchase_source')
    def _onchange_purchase_source(self):
        if self.purchase_source != 'purchase_order':
            self.purchase_order_id = False
        else:
            # Con PO, las facturas salen de la línea: la liga manual no aplica.
            self.account_move_id = False
        if self.purchase_source != 'other':
            self.purchase_method_id = False
            self.payment_details = False

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order_id(self):
        order = self.purchase_order_id
        if self.purchase_line_id and self.purchase_line_id.order_id != order:
            self.purchase_line_id = False
        if order:
            order_date = order.date_approve or order.date_order
            if order_date:
                self.purchase_date = fields.Date.to_date(order_date)
            self.currency_id = order.currency_id

    @api.onchange('purchase_line_id')
    def _onchange_purchase_line_id(self):
        line = self.purchase_line_id
        if line:
            # Costo unitario SIN impuestos (incluye descuentos de la línea).
            qty = line.product_qty
            self.purchase_cost = line.price_subtotal / qty if qty else line.price_unit
            self.currency_id = line.currency_id

    # ==========================================
    # VALIDACIONES
    # ==========================================
    @api.constrains('location_id', 'company_id')
    def _check_location_company(self):
        for asset in self:
            if asset.location_id and asset.location_id.company_id != asset.company_id:
                raise ValidationError(_(
                    "The location %(location)s belongs to another company.",
                    location=asset.location_id.display_name))

    @api.constrains('model_id', 'brand_id')
    def _check_model_brand(self):
        for asset in self:
            if asset.model_id and asset.brand_id and asset.model_id.brand_id != asset.brand_id:
                raise ValidationError(_("The selected model does not belong to the selected brand."))

    @api.constrains('warranty_start', 'warranty_end')
    def _check_warranty_dates(self):
        for asset in self:
            if asset.warranty_start and asset.warranty_end and asset.warranty_end < asset.warranty_start:
                raise ValidationError(_("The warranty end date cannot be before its start date."))

    @api.constrains('registration_date')
    def _check_registration_date(self):
        today = fields.Date.context_today(self)
        for asset in self:
            if asset.registration_date > today:
                raise ValidationError(_("The registration date cannot be in the future."))

    @api.constrains('analytic_distribution')
    def _check_analytic_distribution_total(self):
        # Opcional, pero si se captura debe sumar 100% POR PLAN analítico.
        # Se valida por plan para funcionar igual con llaves simples ("12")
        # que combinadas ("12,34", una cuenta de cada plan en la misma línea).
        Account = self.env['account.analytic.account'].sudo()
        for asset in self:
            if not asset.analytic_distribution:
                continue
            totals = defaultdict(float)
            for key, percentage in asset.analytic_distribution.items():
                for account_id in str(key).split(','):
                    account = Account.browse(int(account_id)).exists()
                    if account:
                        totals[account.root_plan_id.id or account.plan_id.id] += percentage
            if any(float_compare(total, 100.0, precision_digits=2) for total in totals.values()):
                raise ValidationError(_("The analytic distribution of each plan must add up to 100%."))

    # ==========================================
    # CREATE / WRITE / UNLINK
    # ==========================================
    @api.model
    def _normalize_asset_tag(self, tag):
        return re.sub(r'\s+', '', tag or '').upper()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('asset_tag'):
                vals['asset_tag'] = self._normalize_asset_tag(vals['asset_tag'])
        assets = super().create(vals_list)
        assets._create_register_movement()
        return assets

    def write(self, vals):
        if vals.get('asset_tag'):
            vals['asset_tag'] = self._normalize_asset_tag(vals['asset_tag'])
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_without_movements(self):
        # Un activo con historial no se borra: se da de baja con Retire.
        for asset in self:
            if asset.movement_ids.filtered(lambda m: m.movement_type != 'register'):
                raise UserError(_(
                    "The asset %(tag)s already has movements in its history and cannot be deleted. "
                    "Use the Retire action instead.", tag=asset.asset_tag))

    # ==========================================
    # HISTORIAL
    # ==========================================
    def _create_register_movement(self):
        """Primer renglón del historial de cada activo (alta)."""
        vals_list = []
        for asset in self:
            vals_list.append({
                'asset_id': asset.id,
                'movement_type': 'register',
                'date': asset.registration_date,
                'state_to': asset.state,
                'employee_to_id': asset.employee_id.id,
                'department_to_id': asset.assigned_department_id.id,
                'company_to_id': asset.company_id.id,
                'location_to_id': asset.location_id.id,
                'condition_to_id': asset.condition_id.id,
            })
        return self.env['pao.it.asset.movement'].sudo().create(vals_list)

    @api.model
    def _ensure_register_movements(self):
        """Idempotente (se llama en cada actualización del módulo, ver
        data/pao_it_asset_data_update.xml): da su movimiento Register a los
        activos creados antes de que existiera el historial."""
        assets = self.sudo().with_context(active_test=False).search([('movement_ids', '=', False)])
        for asset in assets:
            if asset.create_date and asset.create_date.date() < asset.registration_date:
                asset.registration_date = asset.create_date.date()
        assets._create_register_movement()

    def _get_last_movement(self, movement_types=None):
        """Último movimiento del activo (por fecha efectiva y luego por orden
        de captura), opcionalmente filtrado por tipos."""
        self.ensure_one()
        movements = self.movement_ids
        if movement_types:
            movements = movements.filtered(lambda m: m.movement_type in movement_types)
        return movements.sorted(lambda m: (m.date, m.id))[-1:]

    # ==========================================
    # ACCIONES (abren el asistente de movimientos)
    # ==========================================
    def action_open_movement_wizard(self):
        movement_type = self.env.context.get('movement_type')
        return self._action_movement_wizard(movement_type)

    def _action_movement_wizard(self, movement_type):
        wizard = self.env['pao.it.asset.movement.wizard']
        labels = dict(wizard._fields['movement_type']._description_selection(self.env))
        return {
            'type': 'ir.actions.act_window',
            'name': labels.get(movement_type, _('Movement')),
            'res_model': 'pao.it.asset.movement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_movement_type': movement_type,
                'default_asset_ids': [(6, 0, self.ids)],
            },
        }
