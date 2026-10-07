# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Los importes del encargado de comisiones solo los ve Finanzas o el
# Gerente de Comisiones (también deben ocultarse en las vistas).
_MANAGER_COMMISSION_GROUPS = (
    'pao_sales_commission_management.group_pao_sales_finance_commission,'
    'pao_sales_commission_management.group_pao_sales_commission_manager'
)


class PaoSalesCommission(models.Model):
    _name = 'pao.sales.commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sales Commission Payable'
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Folio', required=True, copy=False, readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'pao.sales.commission'
        ) or 'New',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order', string='Quotation',
        required=True, readonly=True, ondelete='cascade', index=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer',
        related='sale_order_id.partner_id', store=True, readonly=True,
    )
    sales_customer_type = fields.Selection(
        related='partner_id.sales_customer_type', string='Customer Type',
        store=True, readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        related='sale_order_id.company_id', store=True, readonly=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users', string='Quote Salesperson',
        related='sale_order_id.user_id', store=True, readonly=True,
    )

    # -- Comisionista (snapshot al momento de generar el registro) --------
    promotor_id = fields.Many2one(
        comodel_name='comisionpromotores.promotor', string='Promoter',
        required=True, readonly=True,
    )
    promotor_type = fields.Selection(
        selection=[
            ('external', 'External'),
            ('sales', 'Salesperson'),
            ('coordination', 'Coordination'),
        ],
        string='Promoter Type', readonly=True,
    )
    related_user_id = fields.Many2one(
        comodel_name='res.users', string='Related User',
        readonly=True,
        
    )
    commission_percentage = fields.Float(
        string='% commission', readonly=True, digits=(5, 2),
    )

    # -- Montos -------------------------------------------------------------
    currency_cotizacion_id = fields.Many2one(
        comodel_name='res.currency', string='Currency quotation',
        related='sale_order_id.currency_id', store=True, readonly=True,
    )
    currency_mxn_id = fields.Many2one(
        comodel_name='res.currency', string='Payment Currency(MXN)',
        compute='_compute_currency_mxn_id', store=True,
    )
    commissionable_base = fields.Monetary(
        string='Commissionable Base (without taxes)', readonly=True,
        currency_field='currency_cotizacion_id',
    )
    commission_amount = fields.Monetary(
        string='Commission Amount', readonly=True,
        currency_field='currency_cotizacion_id',
    )
    applied_exchange_rate = fields.Float(
        string='Applied Exchange Rate', readonly=True, digits=(12, 6),
    )
    commission_amount_mxn = fields.Monetary(
        string='Commission Amount (MXN)', readonly=True,
        currency_field='currency_mxn_id',
    )
    manager_commission_percentage = fields.Float(
        string='Manager Commission %', digits=(5, 2),
        compute='_compute_manager_commission_percentage', store=True,
        groups=_MANAGER_COMMISSION_GROUPS,
        help='Percentage of the commissionable base that the commissions '
             'manager receives on commissions of Salesperson and '
             'Coordination agents. External agents do not generate it.',
    )
    manager_commission_amount = fields.Monetary(
        string='Manager Commission Amount',
        compute='_compute_manager_commission_amount', store=True,
        currency_field='currency_cotizacion_id',
        groups=_MANAGER_COMMISSION_GROUPS,
    )
    manager_commission_amount_mxn = fields.Monetary(
        string='Manager Commission Amount (MXN)',
        compute='_compute_manager_commission_amount', store=True,
        currency_field='currency_mxn_id',
        groups=_MANAGER_COMMISSION_GROUPS,
    )
    reference_payment_id = fields.Many2one(
        comodel_name='account.payment', string='Reference Payment (E.R.)',
        readonly=True,
        help='Customer payment used to determine the exchange rate '
             '(it was the one with the highest amount in MXN equivalent).',
    )
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order', string='Related Purchase Order',
        readonly=True, copy=False,
        help='Purchase order generated to pay this commission to an '
             'external commission agent, grouped together with other '
             'approved commissions from the same agent.',
    )
    commission_line_ids = fields.One2many(
        comodel_name='pao.sales.commission.line', inverse_name='commission_id',
        string='Commissionable Product Lines',
        help='Product lines this commission is actually being paid on, '
             'copied from the quotation when this commission was generated '
             'and refreshed only when "Recalculate" is clicked. Finance can '
             'lower the commissionable quantity per line without affecting '
             'the quotation itself; the base, commission amount and MXN '
             'amount are recalculated automatically when they do.',
    )

    # -- Validación de servicio (sólo coordinadores) ------------------------
    requires_service_validation = fields.Boolean(
        string='Requires service validation.', 
        compute='_compute_requires_service_validation',
        store=True,
    )
    service_performed = fields.Boolean(
        string='Service Done', readonly=True,
    )
    service_performed_date = fields.Date(
        string='Service End Date', readonly=True,
    )

    # -- Estado / ciclo de aprobación ----------------------------------------
    state = fields.Selection(
        selection=[
            ('pending_invoicing', 'Pending Invoicing'),
            ('pending_service', 'Pending Service (Coordinator)'),
            ('submit_for_approval', 'Submit for Approval'),
            ('pending_approval', 'Pending Approval'),
            ('approved', 'Approved'),
            ('not_approved', 'Not Approved'),
            ('processed', 'Processed'),
            ('under_review', 'Under Review'),
        ],
        string='State', default='pending_invoicing', tracking=True,
        readonly=True, copy=False,
    )
    generation_date = fields.Datetime(
        string='Generation Date', readonly=True,
        default=fields.Datetime.now,
    )
    alert_reason = fields.Text(
        string='Alert Reason', readonly=True, copy=False,
    )
    active = fields.Boolean(default=True)

    # States where a human is actively handling the commission (mid-review,
    # already decided, or flagged) — the cron must not silently change
    # amounts or state under them anymore.
    _FROZEN_STATES = ('pending_approval', 'approved', 'not_approved', 'processed', 'under_review')

    # % de la base comisionable (sin impuestos) que se lleva el encargado de
    # comisiones en comisiones de vendedores y coordinadores.
    _MANAGER_COMMISSION_PERCENTAGE = 1.5

    _sql_constraints = [
        ('sale_order_uniq', 'unique(sale_order_id)',
         'A commission for this quote already exists.'),
    ]

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('promotor_type')
    def _compute_requires_service_validation(self):
        for rec in self:
            rec.requires_service_validation = rec.promotor_type == 'coordination'

    @api.depends('promotor_type')
    def _compute_manager_commission_percentage(self):
        for rec in self:
            rec.manager_commission_percentage = (
                self._MANAGER_COMMISSION_PERCENTAGE
                if rec.promotor_type in ('sales', 'coordination') else 0.0
            )

    @api.depends('commissionable_base', 'manager_commission_percentage',
                 'applied_exchange_rate')
    def _compute_manager_commission_amount(self):
        for rec in self:
            # sudo: quien dispare el recálculo puede no tener acceso de
            # lectura a este campo restringido por grupo.
            amount = rec.commissionable_base * (
                rec.sudo().manager_commission_percentage / 100.0
            )
            rec.manager_commission_amount = amount
            rec.manager_commission_amount_mxn = amount * rec.applied_exchange_rate

    @api.depends()
    def _compute_currency_mxn_id(self):
        mxn = self.env['res.currency'].search([('name', '=', 'MXN')], limit=1)
        for rec in self:
            rec.currency_mxn_id = mxn

    # ------------------------------------------------------------------
    # Botones / acciones manuales
    # ------------------------------------------------------------------
    def action_view_sale(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
        }

    def action_recalculate(self):
        """Botón manual para forzar el recálculo de un registro puntual."""
        for rec in self:
            rec._update_from_sale_order(rec.sale_order_id)
        return True

    # ------------------------------------------------------------------
    # Ciclo de aprobación: Gerente envía a Finanzas, Finanzas aprueba/rechaza.
    # ------------------------------------------------------------------
    def _check_user_in_group(self, group_xmlids, action_label):
        """group_xmlids: un xml_id (str) o varios (tuple); basta con
        pertenecer a uno."""
        if isinstance(group_xmlids, str):
            group_xmlids = (group_xmlids,)
        if not any(
            self.env.user.has_group('pao_sales_commission_management.%s' % xmlid)
            for xmlid in group_xmlids
        ):
            raise UserError(
                'You do not have permission to %s.' % action_label
            )

    def action_submit_for_approval(self):
        """Botón del Gerente de Comisiones: envía la comisión a Finanzas y le
        crea una actividad pendiente a cada usuario de ese grupo."""
        self._check_user_in_group(
            'group_pao_sales_commission_manager', 'submit commissions for approval'
        )
        finance_users = self.env.ref(
            'pao_sales_commission_management.group_pao_sales_finance_commission'
        ).users
        for rec in self:
            if rec.state not in ('submit_for_approval', 'not_approved'):
                raise UserError(
                    'Only commissions in "Submit for Approval" or "Not '
                    'Approved" status can be sent for approval.'
                )
            rec.state = 'pending_approval'
            for user in finance_users:
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary='Commission pending approval: %s' % rec.name,
                    user_id=user.id,
                )
        return True

    def action_approve(self):
        """Botón de Finanzas: aprueba la comisión y cierra la actividad."""
        self._check_user_in_group(
            'group_pao_sales_finance_commission', 'approve commissions'
        )
        for rec in self:
            if rec.state != 'pending_approval':
                raise UserError(
                    'Only commissions "Pending Approval" can be approved.'
                )
            rec.state = 'approved'
            rec._close_approval_activities('Commission approved.')
        return True

    def action_reject(self):
        """Botón de Finanzas o del Gerente de Comisiones: rechaza la
        comisión mientras no esté Aprobada, Procesada ni ya Rechazada. Si
        estaba pendiente de aprobación, cierra las actividades de Finanzas."""
        self._check_user_in_group(
            ('group_pao_sales_finance_commission',
             'group_pao_sales_commission_manager'),
            'reject commissions',
        )
        for rec in self:
            if rec.state in ('approved', 'processed', 'not_approved'):
                raise UserError(
                    'Commissions that are Approved, Processed or already '
                    'Not Approved cannot be rejected.'
                )
            was_pending_approval = rec.state == 'pending_approval'
            rec.state = 'not_approved'
            if was_pending_approval:
                rec._close_approval_activities('Commission not approved.')
        return True

    def action_mark_processed(self):
        """Botón de Finanzas: marca como procesada una comisión Aprobada de
        un vendedor/coordinador (no externo — esos pasan a "Procesado"
        automáticamente al generarles la orden de compra)."""
        self._check_user_in_group(
            'group_pao_sales_finance_commission', 'mark commissions as processed'
        )
        for rec in self:
            if rec.state != 'approved':
                raise UserError(
                    'Only commissions "Approved" can be marked as processed.'
                )
            if rec.promotor_type == 'external':
                raise UserError(
                    'Commissions from an External commission agent are '
                    'marked as processed automatically when their '
                    'purchase order is generated, not with this button.'
                )
            rec.state = 'processed'
        return True

    def _close_approval_activities(self, feedback):
        self.ensure_one()
        todo_type = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False
        )
        activities = self.activity_ids
        if todo_type:
            activities = activities.filtered(
                lambda a: a.activity_type_id == todo_type
            )
        if activities:
            activities.action_feedback(feedback=feedback)

    # ------------------------------------------------------------------
    # Acción masiva del Gerente: generar una orden de compra que agrupe
    # varias comisiones aprobadas de un mismo comisionista externo.
    # ------------------------------------------------------------------
    def action_generate_purchase_order(self):
        self._check_user_in_group(
            'group_pao_sales_commission_manager',
            'generate purchase orders for commissions',
        )
        if not self:
            raise UserError('Select at least one commission.')
        if any(rec.state != 'approved' for rec in self):
            raise UserError(
                'Only commissions in "Approved" status can be used to '
                'generate a purchase order.'
            )
        if any(rec.promotor_type != 'external' for rec in self):
            raise UserError(
                'A purchase order can only be generated for commissions '
                'of an External commission agent.'
            )
        if any(rec.purchase_order_id for rec in self):
            raise UserError(
                'One or more selected commissions already have a related '
                'purchase order.'
            )
        promotores = self.mapped('promotor_id')
        if len(promotores) > 1:
            raise UserError(
                'All selected commissions must belong to the same '
                'commission agent.'
            )
        promotor = promotores
        if not promotor.partner_id:
            raise UserError(
                'The commission agent "%s" has no vendor configured. Set '
                'it in Commissions > Configuration > Commission Agent '
                'before generating a purchase order.' % promotor.name
            )
        product = self.env['product.product'].search(
            [('name', '=', 'Comisiones Promotores')], limit=1
        )
        if not product:
            raise UserError(
                'No product named "Comisiones Promotores" was found in '
                'the product catalog. Create it first.'
            )

        mxn = self.env['res.currency'].search([('name', '=', 'MXN')], limit=1)
        if not mxn:
            mxn = self.env['res.currency'].with_context(
                active_test=False
            ).search([('name', '=', 'MXN')], limit=1)
        if not mxn:
            raise UserError(
                'The MXN currency was not found (or is not active) in '
                'this database.'
            )

        total_mxn = sum(self.mapped('commission_amount_mxn'))
        order_line_vals = {
            'product_id': product.id,
            'name': 'Comisiones Promotores: %s' % ', '.join(self.mapped('name')),
            'product_qty': 1,
            'product_uom': product.uom_po_id.id,
            'price_unit': total_mxn,
            'date_planned': fields.Datetime.now(),
        }
        # Mismo comportamiento que el módulo suppliertaxes (que solo actúa
        # vía onchange en el formulario, por lo que no se dispara al crear
        # la orden directo por código): si el proveedor tiene impuestos de
        # proveedor configurados, se les asignan a la línea; si no, se deja
        # tal cual (sin impuestos), igual que haría el onchange.
        supplier_taxes = promotor.partner_id.st_supplier_taxes_id
        if supplier_taxes:
            order_line_vals['taxes_id'] = [(6, 0, supplier_taxes.taxes_id.ids)]

        purchase_order = self.env['purchase.order'].sudo().create({
            'partner_id': promotor.partner_id.id,
            'currency_id': mxn.id,
            'order_line': [(0, 0, order_line_vals)],
        })
        self.write({
            'purchase_order_id': purchase_order.id,
            'state': 'processed',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id,
        }

    # ------------------------------------------------------------------
    # Cron: punto de entrada principal
    # ------------------------------------------------------------------
    @api.model
    def cron_generate_and_update_commissions(self):
        """Recorre las cotizaciones confirmadas con comisionista asignado y:
        1) Genera el registro de comisión si no existe.
        2) Actualiza su estado/montos si aún no está pagado.
        3) Revisa reversos/cancelaciones en registros ya generados o pagados.
        """
        domain = [
            ('state', '=', 'sale'),
            ('pao_commission_agent_id', '!=', False),
            ('pao_commission_agent_id.commission_rate', '>', 0),
            ('pao_sales_commission_ids', '=', False),
            ('country_code', '=', 'MX'),
        ]
        sales = self.env['sale.order'].search(domain)
        for sale in sales:
            try:
                self._generate_for_sale_order(sale)
            except Exception:  # noqa: BLE001
                _logger.exception(
                    'Error generating commission for the sale %s',
                    sale.name,
                )

        rec_commissions = self.search(
            [('state', 'not in', self._FROZEN_STATES)]
        )
        for r in rec_commissions:
            try:
                r._update_for_sale_order()
            except Exception:  # noqa: BLE001
                _logger.exception(
                    'Error updating commission for the sale %s',
                    sale.name,
                )

        # Revisión de alertas sobre registros existentes (incluye los ya
        # enviados/aprobados, para detectar reversos posteriores).
        records = self.search([
            ('state', 'in', (
                'pending_service', 'submit_for_approval',
                'pending_approval', 'approved', 'processed',
            )),
        ])
        for rec in records:
            try:
                rec._review_reverse_alert()
            except Exception:  # noqa: BLE001
                _logger.exception(
                    'Error checking commission reversal alert %s',
                    rec.name,
                )
        return True

    # ------------------------------------------------------------------
    # Generación / actualización por cotización
    # ------------------------------------------------------------------
    @api.model
    def _update_for_sale_order(self):
        commissionable_base = sum(self.commission_line_ids.mapped('subtotal'))
        if commissionable_base <= 0:
            # No hay nada comisionable en esta venta, no se genera registro.
            return

        if self.state in self._FROZEN_STATES:
            # No se recalcula automáticamente algo que ya está siendo
            # gestionado por una persona (enviado a aprobación, aprobado,
            # rechazado o en revisión); eso requiere intervención manual.
            return

        self.commissionable_base = commissionable_base
        self.commission_amount = commissionable_base * (
            self.commission_percentage / 100.0
        )

        if not self.sale_order_id._commission_is_invoiced_and_paid():
            self.state = 'pending_invoicing'
            return

        invoices = self.sale_order_id._commission_get_invoices().filtered(
            lambda m: m.state == 'posted'
        )
        exchange_rate, better_pay = self._determine_exchange_rate(
            invoices, self.sale_order_id.company_id
        )
        self.applied_exchange_rate = exchange_rate
        self.reference_payment_id = better_pay.id if better_pay else False
        self.commission_amount_mxn = self.commission_amount * exchange_rate

        if self.promotor_type != 'coordination':
            self.state = 'submit_for_approval'
            return

        # Coordinador: validar que el servicio ya se haya realizado.
        done, end_date = self._check_service_performed(self.sale_order_id)
        self.service_performed = done
        self.service_performed_date = end_date or False
        self.state = 'submit_for_approval' if done else 'pending_service'

    @api.model
    def _generate_for_sale_order(self, sale_order):
        promotor = sale_order.pao_commission_agent_id
        if not promotor:
            return
        lineas_comisionables = sale_order._pao_commissionable_lines()
        commissionable_base = sum(lineas_comisionables.mapped('price_subtotal'))
        if commissionable_base <= 0:
            # No hay nada comisionable en esta venta, no se genera registro.
            return
        record = self.search(
            [('sale_order_id', '=', sale_order.id)], limit=1
        )
        if not record:
            record = self.create({
                'sale_order_id': sale_order.id,
                'promotor_id': promotor.id,
                'promotor_type': promotor.promotor_type,
                'related_user_id': promotor.user_id.id,
                'commission_percentage': promotor.commission_rate,
                'commission_line_ids': [
                    (0, 0, self._prepare_commission_line_vals(line))
                    for line in lineas_comisionables
                ],
            })
            record._update_for_sale_order()

    @api.model
    def _prepare_commission_line_vals(self, sale_line):
        return {
            'sale_order_line_id': sale_line.id,
            'product_id': sale_line.product_id.id,
            'original_product_uom_qty': sale_line.product_uom_qty,
            'product_uom_qty': sale_line.product_uom_qty,
            'price_unit': sale_line.price_unit,
            'organization_id': sale_line.organization_id.id,
            'registrynumber_id': sale_line.registrynumber_id.id,
            'service_start_date': sale_line.service_start_date,
            'service_end_date': sale_line.service_end_date,
        }

    def _sync_lines_from_sale_order(self):
        """Resincroniza las líneas de comisión con la cotización (solo se
        dispara a mano desde el botón 'Recalculate'; el cron nunca lo hace).

        - Líneas existentes: se refrescan precio, cantidad vendida,
          organización, registro y fechas. La cantidad comisionable sigue a
          la cantidad vendida solo si Finanzas no la había bajado a mano; si
          la había bajado, se respeta (recortada a la nueva cantidad vendida).
        - Líneas nuevas comisionables de la cotización: se agregan.
        - Líneas que ya no aplican (se quitó el comisionista o el check de
          comisión, o se borró la línea de venta): se eliminan.

        Las operaciones sobre las líneas van con sudo porque el Gerente (que
        también puede recalcular) solo tiene lectura sobre ese modelo."""
        self.ensure_one()
        eligible = self.sale_order_id._pao_commissionable_lines()
        Line = self.env['pao.sales.commission.line'].sudo().with_context(
            pao_skip_commission_recompute=True
        )
        kept_sale_lines = self.env['sale.order.line']
        updated, added, removed = [], [], []

        for line in Line.browse(self.commission_line_ids.ids):
            sale_line = line.sale_order_line_id
            if not sale_line or sale_line not in eligible:
                removed.append(line.product_id.display_name)
                line.unlink()
                continue
            kept_sale_lines |= sale_line
            fresh = self._prepare_commission_line_vals(sale_line)
            fresh.pop('sale_order_line_id')
            untouched = line.product_uom_qty == line.original_product_uom_qty
            if untouched:
                fresh['product_uom_qty'] = fresh['original_product_uom_qty']
            else:
                fresh['product_uom_qty'] = min(
                    line.product_uom_qty, fresh['original_product_uom_qty']
                )
            changes = {}
            for fname, value in fresh.items():
                current = line[fname]
                if isinstance(current, models.BaseModel):
                    current = current.id
                if current != value:
                    changes[fname] = value
            if changes:
                line.write(changes)
                updated.append(line.product_id.display_name)

        for sale_line in eligible - kept_sale_lines:
            vals = self._prepare_commission_line_vals(sale_line)
            vals['commission_id'] = self.id
            Line.create(vals)
            added.append(sale_line.product_id.display_name)

        self.invalidate_recordset(['commission_line_ids'])
        if updated or added or removed:
            parts = []
            if updated:
                parts.append('updated: %s' % ', '.join(updated))
            if added:
                parts.append('added: %s' % ', '.join(added))
            if removed:
                parts.append('removed: %s' % ', '.join(removed))
            self.message_post(
                body='Commission lines synchronized with the quotation (%s).'
                     % '; '.join(parts)
            )

    def _update_from_sale_order(self, sale_order):
        """Wrapper de instancia usado por el botón 'Recalcular': primero
        resincroniza las líneas con la cotización y luego recalcula."""
        self.ensure_one()
        if self.state == 'approved':
            self._refresh_exchange_rate()
            return
        if self.state in self._FROZEN_STATES:
            raise UserError(
                'A commission that has already been sent for approval, '
                'not approved, processed, or is under review cannot be '
                'recalculated. Contact the Commissions Manager or Finance '
                'if an adjustment is required.'
            )
        self._sync_lines_from_sale_order()
        if sum(self.commission_line_ids.mapped('subtotal')) <= 0:
            # Al lanzar el error se revierte también la resincronización.
            raise UserError(
                'After synchronizing with the quotation there would be no '
                'commissionable lines with an amount left to pay. Review '
                'the quotation (commissionable products and their '
                'commission agent) before recalculating.'
            )
        self._update_for_sale_order()

    def _refresh_exchange_rate(self):
        """Recalcular sobre una comisión ya Aprobada: solo se vuelve a
        determinar el tipo de cambio (y con él el importe en MXN); las
        líneas, la base y el importe en moneda de la cotización, que
        Finanzas ya aprobó, no se tocan ni el estado cambia."""
        self.ensure_one()
        self._check_user_in_group(
            ('group_pao_sales_finance_commission',
             'group_pao_sales_commission_manager'),
            'recalculate approved commissions',
        )
        # sudo: los facturas/pagos pueden no ser legibles para el Gerente.
        sale = self.sale_order_id.sudo()
        if not sale._commission_is_invoiced_and_paid():
            raise UserError(
                'The quotation is no longer fully invoiced and paid; the '
                'exchange rate was not refreshed. Review the invoices.'
            )
        invoices = sale._commission_get_invoices().filtered(
            lambda m: m.state == 'posted'
        )
        exchange_rate, better_pay = self.sudo()._determine_exchange_rate(
            invoices, sale.company_id
        )
        if not exchange_rate:
            raise UserError(
                'The exchange rate could not be determined (no related '
                'payments or USD/MXN currencies not found).'
            )
        old_rate = self.applied_exchange_rate
        old_mxn = self.commission_amount_mxn
        self.applied_exchange_rate = exchange_rate
        self.reference_payment_id = better_pay.id
        self.commission_amount_mxn = self.commission_amount * exchange_rate
        if old_rate != exchange_rate:
            self.message_post(
                body='Exchange rate refreshed on an approved commission: '
                     '%s -> %s (commission MXN %s -> %s).' % (
                         old_rate, exchange_rate,
                         old_mxn, self.commission_amount_mxn,
                     )
            )

    # ------------------------------------------------------------------
    # Cálculo de tipo de cambio (pago de mayor monto en equivalente MXN)
    # ------------------------------------------------------------------
    def _get_related_payments(self, invoices):
        """Regresa los account.payment conciliados contra las líneas por
        cobrar (receivable) de las facturas indicadas."""
        if not invoices:
            return self.env['account.payment']
        receivable_lines = invoices.line_ids.filtered(
            lambda l: l.account_id.account_type in (
                'asset_receivable', 'liability_payable'
            )
        )
        partials = receivable_lines.matched_debit_ids | receivable_lines.matched_credit_ids
        other_lines = (
            partials.mapped('debit_move_id') | partials.mapped('credit_move_id')
        ) - receivable_lines
        payments = other_lines.mapped('move_id.payment_id')
        return payments.filtered(lambda p: p)

    def _determine_exchange_rate(self, invoices, company):
        """Devuelve (tipo_cambio_usd_mxn, account.payment): se usa la fecha
        del pago de mayor monto (ya convertido a MXN) entre los pagos
        conciliados a las facturas relacionadas. Si dos o más pagos empatan
        en el monto en MXN, se toma el más antiguo (fecha de pago más
        temprana) entre ellos, en vez de depender del orden implícito del
        recordset."""
        self.ensure_one()
        mxn = self.env['res.currency'].search([('name', '=', 'MXN')], limit=1)
        usd = self.currency_cotizacion_id or self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1
        )
        if not mxn or not usd:
            _logger.warning(
                'USD/MXN currencies configured in the system were not found; '
                'the exchange rate for %s cannot be calculated',
                self.name,
            )
            return 0.0, self.env['account.payment']

        payments = self._get_related_payments(invoices)
        if not payments:
            return 0.0, self.env['account.payment']

        better_payment = self.env['account.payment']
        better_amount_mxn = -1.0
        better_date = None
        for payment in payments:
            date = payment.date or fields.Date.context_today(self)
            amount_mxn = payment.currency_id._convert(
                payment.amount, mxn, company, date
            )
            is_better = amount_mxn > better_amount_mxn or (
                amount_mxn == better_amount_mxn and date < better_date
            )
            if is_better:
                better_amount_mxn = amount_mxn
                better_payment = payment
                better_date = date

        if not better_payment:
            return 0.0, self.env['account.payment']

        better_payment_date = better_payment.date or fields.Date.context_today(self)
        # round=False: _convert redondea a los decimales de MXN (2) y eso
        # truncaría el tipo de cambio (17.8413 -> 17.84).
        exchange_rate = usd._convert(
            1.0, mxn, company, better_payment_date, round=False
        )
        return exchange_rate, better_payment

    # ------------------------------------------------------------------
    # Validación de servicio realizado (coordinadores)
    # ------------------------------------------------------------------
    def _check_service_performed(self, sale_order):
        """Revisa las órdenes de compra relacionadas (purchase_order_id) y
        sus líneas (vía sra_sale_line_ids) para saber si el servicio
        contratado ya finalizó (service_end_date <= hoy), ignorando órdenes
        de compra canceladas.

        Devuelve (True/False, fecha_fin_relevante_o_False).
        """
        self.ensure_one()
        purchase_orders = sale_order.purchase_order_id.filtered(
            lambda po: po.state != 'cancel'
        )
        commissionable_sales_lines = self.commission_line_ids.mapped('sale_order_line_id')
        if not purchase_orders or not commissionable_sales_lines:
            # No hay evidencia de servicio contratado: se deja pendiente
            # para revisión manual de finanzas en vez de aprobarlo solo.
            return False, False

        purchase_lines = purchase_orders.order_line.filtered(
            lambda pl: pl.sra_sale_line_ids & commissionable_sales_lines
        )
        if not purchase_lines:
            return False, False

        if any(not pl.service_end_date for pl in purchase_lines):
            return False, False

        today = fields.Date.context_today(self)
        if any(pl.service_end_date > today for pl in purchase_lines):
            return False, False

        date_max = max(purchase_lines.mapped('service_end_date'))
        return True, date_max

    # ------------------------------------------------------------------
    # Alertas por reverso/cancelación posterior a la generación o al pago
    # ------------------------------------------------------------------
    def _review_reverse_alert(self):
        self.ensure_one()
        sale = self.sale_order_id
        problem, reason = sale._commission_has_billing_issue()

        if not problem and sale.state == 'cancel':
            problem, reason = True, 'The quote/sale was cancelled.'

        if not problem and self.promotor_type == 'coordination' and \
                self.state in ('submit_for_approval', 'pending_approval', 'approved', 'processed'):
            # Si ya se había marcado servicio realizado, pero la orden de
            # compra que lo sustentaba fue cancelada después, se re-valida.
            done, _fecha = self._check_service_performed(sale)
            if not done and self.service_performed:
                problem = True
                reason = ('The purchase order verifying the service performed '
                          'was cancelled or modified.')

        if problem:
            self.write({
                'state': 'under_review',
                'alert_reason': reason,
            })
            self.message_post(
                body=('⚠️ Commission alert: %s Review before proceeding '
                      'with the payment.') % reason
            )
