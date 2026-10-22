from odoo import fields

# ==========================================
# REGLAS COMUNES DE COSTOS (activo y tablero)
# ==========================================
# Un solo lugar para: cómo se convierte a USD y con qué fecha se ubica cada
# gasto. Los usan la pestaña Costs del activo y el tablero, para que ambos
# den siempre los mismos números.


def usd_currency(env):
    return env.ref('base.USD')


def to_usd(env, amount, currency, company, date):
    """Monto en USD con el tipo de cambio HISTÓRICO de `date` (los tipos se
    actualizan a diario en las 4 compañías)."""
    if not amount:
        return 0.0
    company = company.sudo() or env.company
    currency = currency or company.currency_id
    return currency._convert(amount, usd_currency(env), company, date or fields.Date.context_today(env.user),
                             round=False)


def maintenance_cost_date(maintenance):
    # Fecha de fin → inicio → programada.
    return maintenance.end_date or maintenance.start_date or maintenance.scheduled_date


def movement_shipping_date(movement):
    return movement.ship_date or movement.date


def maintenance_shipping_date(maintenance):
    return maintenance.ship_date or maintenance_cost_date(maintenance)


def asset_cost_items(asset):
    """Partidas de costo de un activo: (fecha, concepto, referencia, monto,
    moneda, USD). Conceptos: acquisition / maintenance / warranty / shipping.
    Los mantenimientos cancelados no cuentan."""
    env = asset.env
    company = asset.company_id
    items = []
    if asset.purchase_cost:
        items.append({
            'date': asset.purchase_date, 'concept': 'acquisition',
            'reference': asset.purchase_order_ref or asset.purchase_method_id.name or '',
            'amount': asset.purchase_cost, 'currency': asset.currency_id,
            'usd': to_usd(env, asset.purchase_cost, asset.currency_id, company, asset.purchase_date),
        })
    for maintenance in asset.maintenance_ids.filtered(lambda m: m.state != 'cancelled'):
        concept = 'warranty' if maintenance.maintenance_type == 'warranty' else 'maintenance'
        if maintenance.cost:
            date = maintenance_cost_date(maintenance)
            items.append({
                'date': date, 'concept': concept, 'reference': maintenance.name,
                'amount': maintenance.cost, 'currency': maintenance.currency_id,
                'usd': to_usd(env, maintenance.cost, maintenance.currency_id, company, date),
            })
        if maintenance.shipping_cost:
            date = maintenance_shipping_date(maintenance)
            items.append({
                'date': date, 'concept': 'shipping', 'reference': maintenance.name,
                'amount': maintenance.shipping_cost, 'currency': maintenance.shipping_currency_id,
                'usd': to_usd(env, maintenance.shipping_cost, maintenance.shipping_currency_id, company, date),
            })
    for movement in asset.movement_ids.filtered('shipping_cost'):
        date = movement_shipping_date(movement)
        items.append({
            'date': date, 'concept': 'shipping',
            'reference': movement.tracking_number or movement.display_name,
            'amount': movement.shipping_cost, 'currency': movement.shipping_currency_id,
            'usd': to_usd(env, movement.shipping_cost, movement.shipping_currency_id,
                          movement.company_from_id or company, date),
        })
    return sorted(items, key=lambda i: (i['date'] or fields.Date.to_date('1900-01-01')))
