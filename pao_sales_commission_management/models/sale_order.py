# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pao_sales_commission_ids = fields.One2many(
        comodel_name='pao.sales.commission',
        inverse_name='sale_order_id',
        string='Commissions',
    )
    pao_sales_commission_count = fields.Integer(
        string='# Commissions',
        compute='_compute_pao_sales_commission_count',
    )

    def _compute_pao_sales_commission_count(self):
        for order in self:
            order.pao_sales_commission_count = len(order.pao_sales_commission_ids)

    def action_view_commissions(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'pao_sales_commission_management.action_pao_sales_commission'
        )
        action['domain'] = [('sale_order_id', '=', self.id)]
        action['context'] = {'default_sale_order_id': self.id}
        return action

    # ------------------------------------------------------------------
    # Propagación del promotor del encabezado (pao_promotor_id) a las líneas
    # comisionables. El usuario puede después quitar manualmente el promotor
    # de una línea puntual para excluirla de la comisión; si vuelve a cambiar
    # el promotor del encabezado, se reinician (sobrescriben) todas las
    # líneas comisionables con el nuevo valor.
    # ------------------------------------------------------------------
    def _pao_sync_promotor_to_lines(self):
        for order in self:
            commissionable_lines = order.order_line.filtered(
                lambda l: l.product_id.pao_commission_payment
            )
            commissionable_lines.write({'pao_promotor_id': order.pao_promotor_id.id})

    @api.onchange('pao_promotor_id')
    def _onchange_pao_promotor_id_sync_lines(self):
        for order in self:
            for line in order.order_line.filtered(
                lambda l: l.product_id.pao_commission_payment
            ):
                line.pao_promotor_id = order.pao_promotor_id

    def write(self, vals):
        res = super().write(vals)
        if 'pao_promotor_id' in vals:
            self._pao_sync_promotor_to_lines()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders.filtered('pao_promotor_id')._pao_sync_promotor_to_lines()
        return orders

    # ------------------------------------------------------------------
    # Helpers usados por pao.sales.commission para saber si ya se puede generar
    # (o revisar) la comisión de una cotización.
    # ------------------------------------------------------------------
    def _pao_commissionable_lines(self):
        """Líneas de venta que entran en el cálculo de la comisión: producto
        marcado como comisionable y con un comisionista asignado a nivel de
        línea (el usuario puede excluir una línea puntual quitándole el
        comisionista)."""
        self.ensure_one()
        return self.order_line.filtered(
            lambda l: l.product_id.pao_commission_payment and l.pao_promotor_id
        )

    def _commission_get_invoices(self):
        """Facturas de cliente (posteadas o no) ligadas a esta cotización."""
        self.ensure_one()
        return self.invoice_ids.filtered(
            lambda m: m.move_type == 'out_invoice'
        )

    def _commission_is_invoiced_and_paid(self):
        """True si la cotización ya no tiene nada pendiente de facturar y
        todas sus facturas de cliente (no canceladas) están totalmente
        pagadas."""
        self.ensure_one()
        if self.invoice_status != 'invoiced':
            return False
        facturas = self._commission_get_invoices().filtered(
            lambda m: m.state == 'posted'
        )
        if not facturas:
            return False
        return all(f.payment_state in ('paid', 'in_payment') for f in facturas)

    def _commission_has_billing_issue(self):
        """Detecta si la cotización DEJÓ de estar totalmente facturada y
        pagada después de haberlo estado (una factura se canceló sin
        reemplazo, o un pago se deshizo/desconcilió). Se usa para marcar
        en_revision en comisiones ya generadas o pagadas.

        Reutiliza _commission_is_invoiced_and_paid(), que ya ignora facturas
        canceladas: si una factura se canceló pero fue reemplazada por una
        nueva factura válida y pagada, la cotización sigue "facturada y
        pagada" y esto NO debe marcarse como problema (es una corrección de
        facturación normal, no un reverso)."""
        self.ensure_one()
        if self._commission_is_invoiced_and_paid():
            return False, False
        posted_invoices = self._commission_get_invoices().filtered(
            lambda m: m.state == 'posted'
        )
        if not posted_invoices:
            return True, ('The quotation no longer has a valid posted '
                           'invoice covering the sale (it may have been '
                           'cancelled without a replacement).')
        return True, ('A related invoice is no longer marked as paid '
                       '(possible payment reversal/unreconciliation), or '
                       'the quotation is no longer fully invoiced.')
