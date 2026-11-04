# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class PaoSalesCommissionReport(models.Model):
    """Análisis a nivel línea comisionable (una fila por producto de cada
    comisión): qué producto/cantidad se comisiona, a quién, cuánto le toca
    por esa línea y la fecha del pago que se tomó para el tipo de cambio."""
    _name = 'pao.sales.commission.report'
    _description = 'Commission Product Lines Analysis'
    _auto = False
    _order = 'payment_date desc, commission_id desc, id'

    commission_id = fields.Many2one(
        'pao.sales.commission', string='Commission', readonly=True)
    sale_order_id = fields.Many2one(
        'sale.order', string='Quotation', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True)
    sales_customer_type = fields.Selection(
        selection=lambda self: self.env['res.partner']._fields[
            'sales_customer_type'].selection,
        string='Customer Type', readonly=True)
    promotor_id = fields.Many2one(
        'comisionpromotores.promotor', string='Commission Agent',
        readonly=True)
    promotor_type = fields.Selection(
        selection=lambda self: self.env['pao.sales.commission']._fields[
            'promotor_type'].selection,
        string='Promoter Type', readonly=True)
    state = fields.Selection(
        selection=lambda self: self.env['pao.sales.commission']._fields[
            'state'].selection,
        string='State', readonly=True)
    generation_date = fields.Datetime(string='Generation Date', readonly=True)

    product_id = fields.Many2one(
        'product.product', string='Product', readonly=True)
    sold_qty = fields.Float(string='Qty Sold', readonly=True)
    commissionable_qty = fields.Float(
        string='Commissionable Qty', readonly=True)

    currency_id = fields.Many2one(
        'res.currency', string='Quotation Currency', readonly=True)
    currency_mxn_id = fields.Many2one(
        'res.currency', string='MXN Currency', readonly=True)
    price_unit = fields.Monetary(
        string='Unit Price', readonly=True, currency_field='currency_id')
    currency_usd_id = fields.Many2one(
        'res.currency', string='USD Currency', readonly=True)
    commissionable_base = fields.Monetary(
        string='Commissionable Base (USD)', readonly=True,
        currency_field='currency_usd_id',
        help='Commissionable base of the line always expressed in USD. '
             'Quotations in USD are taken as they are; quotations in any '
             'other currency (e.g. MXN) are converted to USD with the '
             'exchange rate of the day of the payment assigned to the '
             'commission (or the rate of today when the commission has no '
             'payment yet).')
    commission_percentage = fields.Float(
        string='% Commission', readonly=True, digits=(5, 2))
    commission_amount = fields.Monetary(
        string='Commission Amount', readonly=True,
        currency_field='currency_id',
        help='Commission on this line, in the quotation currency.')
    applied_exchange_rate = fields.Float(
        string='Applied Exchange Rate', readonly=True, digits=(12, 6))
    commission_amount_mxn = fields.Monetary(
        string='Commission Amount (MXN)', readonly=True,
        currency_field='currency_mxn_id',
        help='Commission on this line converted to MXN with the exchange '
             'rate of the reference payment (0 until the quotation is '
             'invoiced and paid).')
    payment_date = fields.Date(
        string='Exchange Rate Payment Date', readonly=True,
        help='Date of the payment whose exchange rate was used for the '
             'commission.')

    @api.model
    def _rate_sql(self, currency_expr, date_expr):
        """Subconsulta con la misma lógica que res.currency._get_rates:
        tasa vigente a la fecha (primero la de la compañía, luego la global),
        si no hay, la más antigua, y 1.0 si no existe ninguna."""
        return """COALESCE(
            (SELECT r.rate FROM res_currency_rate r
              WHERE r.currency_id = %(cur)s AND r.name <= %(date)s
                AND (r.company_id IS NULL OR r.company_id = c.company_id)
              ORDER BY r.company_id, r.name DESC LIMIT 1),
            (SELECT r.rate FROM res_currency_rate r
              WHERE r.currency_id = %(cur)s
                AND (r.company_id IS NULL OR r.company_id = c.company_id)
              ORDER BY r.company_id, r.name ASC LIMIT 1),
            1.0)""" % {'cur': currency_expr, 'date': date_expr}

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        rate_date = 'COALESCE(pm.date, CURRENT_DATE)'
        rate_quote = self._rate_sql('c.currency_cotizacion_id', rate_date)
        rate_usd = self._rate_sql('usd.id', rate_date)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %(table)s AS (
                SELECT
                    l.id AS id,
                    c.id AS commission_id,
                    c.sale_order_id AS sale_order_id,
                    c.partner_id AS partner_id,
                    c.company_id AS company_id,
                    c.sales_customer_type AS sales_customer_type,
                    c.promotor_id AS promotor_id,
                    c.promotor_type AS promotor_type,
                    c.state AS state,
                    c.generation_date AS generation_date,
                    l.product_id AS product_id,
                    l.original_product_uom_qty AS sold_qty,
                    l.product_uom_qty AS commissionable_qty,
                    c.currency_cotizacion_id AS currency_id,
                    c.currency_mxn_id AS currency_mxn_id,
                    l.price_unit AS price_unit,
                    usd.id AS currency_usd_id,
                    CASE
                        WHEN usd.id IS NULL THEN NULL
                        WHEN c.currency_cotizacion_id = usd.id THEN l.subtotal
                        ELSE ROUND((COALESCE(l.subtotal, 0)
                                    / %(rate_quote)s * %(rate_usd)s)::numeric, 2)
                    END AS commissionable_base,
                    c.commission_percentage AS commission_percentage,
                    ROUND((COALESCE(l.subtotal, 0)
                           * COALESCE(c.commission_percentage, 0) / 100.0)::numeric, 2)
                        AS commission_amount,
                    c.applied_exchange_rate AS applied_exchange_rate,
                    ROUND((COALESCE(l.subtotal, 0)
                           * COALESCE(c.commission_percentage, 0) / 100.0
                           * COALESCE(c.applied_exchange_rate, 0))::numeric, 2)
                        AS commission_amount_mxn,
                    pm.date AS payment_date
                FROM pao_sales_commission_line l
                JOIN pao_sales_commission c ON c.id = l.commission_id
                LEFT JOIN account_payment p ON p.id = c.reference_payment_id
                LEFT JOIN account_move pm ON pm.id = p.move_id
                LEFT JOIN LATERAL (
                    SELECT id FROM res_currency WHERE name = 'USD' LIMIT 1
                ) usd ON TRUE
                WHERE c.active IS NOT FALSE
            )
        """ % {
            'table': self._table,
            'rate_quote': rate_quote,
            'rate_usd': rate_usd,
        })
