from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


# ==========================================
# PERIODO DE UNA SUSCRIPCIÓN (ciclo de contrato)
# ==========================================
# Cada renovación es un periodo con su propio costo, así el precio de un año
# nunca sobrescribe al del anterior y se puede medir el aumento. El periodo
# ES el contrato (número de contrato + contrato adjunto).
#
# Costo (sin capturas a mano de totales, para evitar los descuadres del Excel):
#   - Per user:  cargo por cobro = costo unitario × licencias compradas.
#   - Flat fee:  cargo por cobro capturado directamente.
#   - Perpetual: pago único (frecuencia One-time).
#   - Total del periodo = cargo por cobro × número de cobros del periodo.
class PaoItSubscriptionPeriod(models.Model):
    _name = 'pao.it.subscription.period'
    _description = 'Subscription Period'
    _order = 'subscription_id, start_date desc'
    _rec_names_search = ['subscription_id.software_id.name', 'contract_number']

    subscription_id = fields.Many2one('pao.it.subscription', string='Subscription', required=True,
                                      ondelete='cascade', index=True)
    company_id = fields.Many2one(related='subscription_id.company_id', store=True, index=True)
    software_id = fields.Many2one(related='subscription_id.software_id', store=True)
    license_type = fields.Selection(related='subscription_id.license_type')

    start_date = fields.Date(string='Start Date', required=True)
    # Opcional solo en licencias perpetuas.
    end_date = fields.Date(string='End Date')
    contract_number = fields.Char(string='Contract No.')
    billing_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('one_time', 'One-time'),
    ], string='Billing Frequency', required=True, default='yearly')

    # --- CANTIDADES ---
    # Permitidos = compradas × usuarios por licencia (WPS: 6 × 3 = 18). Por
    # defecto 1 usuario por licencia (Google Workspace: 46 × 1). Decisión del
    # usuario 2026-09-28 (antes era un total capturado a mano).
    licenses_purchased = fields.Integer(string='Licenses Purchased', default=1)
    users_per_license = fields.Integer(string='Users per License', default=1,
                                       help="How many people can use each license (e.g. WPS: 3).")
    allowed_users = fields.Integer(string='Allowed Users', compute='_compute_allowed_users', store=True,
                                   help="Licenses purchased × users per license. "
                                        "Compared against the active assignments.")

    # --- COSTO ---
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    unit_cost = fields.Monetary(string='Unit Cost', currency_field='currency_id',
                                help="Cost per license per billing (per-user licenses).")
    billing_amount = fields.Monetary(string='Amount per Billing', currency_field='currency_id',
                                     compute='_compute_billing_amount', store=True, readonly=False)
    billing_count = fields.Integer(string='Billings in Period', compute='_compute_totals', store=True)
    total_amount = fields.Monetary(string='Period Total', currency_field='currency_id',
                                   compute='_compute_totals', store=True)

    # --- AUMENTO CONTRA EL PERIODO ANTERIOR ---
    previous_period_id = fields.Many2one('pao.it.subscription.period', string='Previous Period',
                                         compute='_compute_increase')
    increase_comparable = fields.Boolean(compute='_compute_increase')
    unit_increase = fields.Monetary(string='Unit Price Change', currency_field='currency_id',
                                    compute='_compute_increase')
    unit_increase_pct = fields.Float(string='Unit Price Change (%)', compute='_compute_increase')
    total_increase = fields.Monetary(string='Total Change', currency_field='currency_id',
                                     compute='_compute_increase')
    total_increase_pct = fields.Float(string='Total Change (%)', compute='_compute_increase')

    # --- COMPRA (mismo esquema que el activo de hardware) ---
    purchase_source = fields.Selection([
        ('purchase_order', 'Purchase Order'),
        ('other', 'Other Purchase Method'),
    ], string='Purchase Source')
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order',
        domain="[('company_id', '=', company_id), ('state', 'in', ('purchase', 'done'))]")
    purchase_line_id = fields.Many2one(
        'purchase.order.line', string='Purchase Order Line',
        domain="[('order_id', '=', purchase_order_id), ('display_type', '=', False)]")
    purchase_order_ref = fields.Char(related='purchase_order_id.name', string='Purchase Order Ref.',
                                     store=True)
    vendor_id = fields.Many2one(related='purchase_order_id.partner_id', string='Vendor', store=True)
    purchase_method_id = fields.Many2one('pao.it.purchase.method', string='Other Purchase Method',
                                         ondelete='restrict')
    payment_details = fields.Char(string='Payment Details',
                                  help="How it was paid, e.g. corporate card, reimbursement.")
    purchase_move_ids = fields.Many2many('account.move', string='Vendor Bills',
                                         compute='_compute_purchase_moves', compute_sudo=True)
    purchase_move_summary = fields.Char(string='Vendor Bills Summary',
                                        compute='_compute_purchase_moves', compute_sudo=True)
    account_move_id = fields.Many2one(
        'account.move', string='Vendor Bill / Journal Entry',
        domain="[('company_id', '=', company_id), ('move_type', 'in', ('in_invoice', 'in_refund', 'entry'))]")
    account_move_ref = fields.Char(related='account_move_id.name', string='Vendor Bill / Journal Entry Ref.',
                                   store=True)

    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', 'pao_it_subscription_period_attachment_rel',
                                      'period_id', 'attachment_id', string='Contract / Attachments')

    # ==========================================
    # CÁLCULOS
    # ==========================================
    @api.depends('start_date', 'end_date', 'subscription_id.display_name')
    def _compute_display_name(self):
        for period in self:
            dates = f"{period.start_date or ''} → {period.end_date or '∞'}"
            period.display_name = f"{period.subscription_id.display_name}: {dates}"

    @api.depends('licenses_purchased', 'users_per_license')
    def _compute_allowed_users(self):
        for period in self:
            period.allowed_users = period.licenses_purchased * period.users_per_license

    @api.model
    def _migrate_users_per_license(self):
        """Idempotente (data/pao_it_asset_data_update.xml). Periodos
        capturados cuando "usuarios permitidos" era un total a mano: deduce
        los usuarios por licencia (18 / 6 = 3) y recalcula el total."""
        self.env.flush_all()
        self.env.cr.execute("""
            UPDATE pao_it_subscription_period
               SET users_per_license = allowed_users / licenses_purchased
             WHERE licenses_purchased > 0
               AND allowed_users > licenses_purchased
               AND MOD(allowed_users, licenses_purchased) = 0
               AND COALESCE(users_per_license, 1) = 1
        """)
        periods = self.sudo().with_context(active_test=False).search([])
        periods.invalidate_recordset(['users_per_license'])
        self.env.add_to_compute(self._fields['allowed_users'], periods)
        periods._recompute_recordset(['allowed_users'])

    @api.depends('license_type', 'unit_cost', 'licenses_purchased')
    def _compute_billing_amount(self):
        for period in self:
            if period.license_type == 'per_user':
                period.billing_amount = period.unit_cost * period.licenses_purchased
            else:
                # Flat fee / perpetual: se captura a mano; se conserva.
                period.billing_amount = period.billing_amount or 0.0

    @api.depends('billing_frequency', 'billing_amount', 'start_date', 'end_date')
    def _compute_totals(self):
        for period in self:
            count = 1
            if period.billing_frequency != 'one_time' and period.start_date and period.end_date:
                span = relativedelta(period.end_date + timedelta(days=1), period.start_date)
                months = span.years * 12 + span.months + (1 if span.days else 0)
                count = months if period.billing_frequency == 'monthly' else -(-months // 12)
            period.billing_count = max(count, 1)
            period.total_amount = period.billing_amount * period.billing_count

    def _unit_reference(self):
        """Precio comparable: el costo unitario (per user) o el cargo por
        cobro (flat fee / perpetual)."""
        self.ensure_one()
        return self.unit_cost if self.license_type == 'per_user' else self.billing_amount

    @api.depends('start_date', 'currency_id', 'unit_cost', 'billing_amount', 'total_amount',
                 'subscription_id.period_ids.start_date')
    def _compute_increase(self):
        for period in self:
            previous = period.subscription_id.period_ids.filtered(
                lambda p: p.start_date and period.start_date and p.start_date < period.start_date
            ).sorted('start_date')[-1:]
            comparable = bool(previous) and previous.currency_id == period.currency_id
            period.previous_period_id = previous
            period.increase_comparable = comparable
            if not comparable:
                period.unit_increase = period.unit_increase_pct = 0.0
                period.total_increase = period.total_increase_pct = 0.0
                continue
            prev_unit, unit = previous._unit_reference(), period._unit_reference()
            period.unit_increase = unit - prev_unit
            period.unit_increase_pct = (unit - prev_unit) / prev_unit * 100 if prev_unit else 0.0
            period.total_increase = period.total_amount - previous.total_amount
            period.total_increase_pct = ((period.total_amount - previous.total_amount) / previous.total_amount * 100
                                         if previous.total_amount else 0.0)

    @api.depends('purchase_source', 'purchase_line_id.invoice_lines.move_id.state')
    def _compute_purchase_moves(self):
        state_labels = dict(self.env['account.move']._fields['state']._description_selection(self.env))
        for period in self:
            moves = self.env['account.move']
            if period.purchase_source == 'purchase_order' and period.purchase_line_id:
                moves = period.purchase_line_id.invoice_lines.move_id.filtered(
                    lambda m: m.move_type in ('in_invoice', 'in_refund') and m.state in ('draft', 'posted'))
            period.purchase_move_ids = moves
            period.purchase_move_summary = ', '.join(
                f"{move.name or '/'} ({state_labels.get(move.state)})" for move in moves)

    # ==========================================
    # ONCHANGES
    # ==========================================
    @api.onchange('license_type')
    def _onchange_license_type(self):
        if self.license_type == 'perpetual':
            self.billing_frequency = 'one_time'

    @api.onchange('purchase_source')
    def _onchange_purchase_source(self):
        if self.purchase_source != 'purchase_order':
            self.purchase_order_id = False
        else:
            self.account_move_id = False
        if self.purchase_source != 'other':
            self.purchase_method_id = False
            self.payment_details = False

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order_id(self):
        if self.purchase_line_id and self.purchase_line_id.order_id != self.purchase_order_id:
            self.purchase_line_id = False
        if self.purchase_order_id:
            self.currency_id = self.purchase_order_id.currency_id

    @api.onchange('purchase_line_id')
    def _onchange_purchase_line_id(self):
        line = self.purchase_line_id
        if line:
            qty = line.product_qty
            unit = line.price_subtotal / qty if qty else line.price_unit
            self.currency_id = line.currency_id
            if self.license_type == 'per_user':
                self.unit_cost = unit
            else:
                self.billing_amount = line.price_subtotal

    # ==========================================
    # CREATE / VALIDACIONES
    # ==========================================
    @api.constrains('start_date', 'end_date', 'subscription_id')
    def _check_dates(self):
        for period in self:
            if period.end_date and period.end_date < period.start_date:
                raise ValidationError(_("The end date of a period cannot be before its start date."))
            if not period.end_date and period.subscription_id.license_type != 'perpetual':
                raise ValidationError(_("The end date is required (it is optional only for perpetual licenses)."))
            far_future = fields.Date.to_date('9999-12-31')
            end = period.end_date or far_future
            for other in period.subscription_id.period_ids - period:
                other_end = other.end_date or far_future
                if other.start_date <= end and period.start_date <= other_end:
                    raise ValidationError(_(
                        "The periods of a subscription cannot overlap (%(period)s overlaps %(other)s).",
                        period=period.display_name, other=other.display_name))

    @api.constrains('licenses_purchased', 'users_per_license')
    def _check_quantities(self):
        for period in self:
            if period.licenses_purchased < 0:
                raise ValidationError(_("Quantities cannot be negative."))
            if period.users_per_license < 1:
                raise ValidationError(_("Users per license must be at least 1."))

    # ==========================================
    # ACCIONES
    # ==========================================
    def action_price_change(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Price Change'),
            'res_model': 'pao.it.subscription.price.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_period_id': self.id,
                'default_new_unit_cost': self.unit_cost,
                'default_new_billing_amount': self.billing_amount,
            },
        }

    def _split_at(self, effective_date, new_unit_cost, new_billing_amount):
        """Parte el periodo en la fecha efectiva de un cambio de precio: el
        tramo anterior conserva el precio, el nuevo tramo toma el nuevo."""
        self.ensure_one()
        if effective_date <= self.start_date or (self.end_date and effective_date > self.end_date):
            raise UserError(_("The effective date must be after the start of the period and within it."))
        vals = self.copy_data({
            'start_date': effective_date,
            'end_date': self.end_date,
            'unit_cost': new_unit_cost,
            'billing_amount': (new_unit_cost * self.licenses_purchased if self.license_type == 'per_user'
                               else new_billing_amount),
            'account_move_id': False,
        })[0]
        # Primero se recorta el tramo anterior (para que no se traslapen).
        self.end_date = effective_date - timedelta(days=1)
        return self.create(vals)
