"""Lógica pura (sin ORM) del comparativo de coordinación por temporada.

Parte de registros "base" al grano más fino, uno por (coordinador, esquema,
cliente), con la cantidad ordenada por mes en cada temporada:
    coord_id, coord_name, scheme_id, scheme_name, scheme_seq, partner_id, partner_name,
    group_name, promotor_name, months {'09': [cant_A, cant_B], ...}

De ahí arma tres vistas: por coordinador, por coordinador y esquema, y por
esquema con sus clientes (igual que el comparativo de facturación, pero solo
cantidades). Reusa las reglas de temporada y variación de billing_report.
"""
import io

try:
    from . import billing_report as br
except ImportError:  # pruebas fuera de Odoo
    import billing_report as br

MONTHS = br.MONTHS
MONTHS_ORDER = br.MONTHS_ORDER


# ----------------------------------------------------------------------
# Cálculos
# ----------------------------------------------------------------------

def zero_months():
    return {m: [0.0, 0.0] for m in MONTHS_ORDER}


def totals(months):
    return sum(c[0] for c in months.values()), sum(c[1] for c in months.values())


def status_of(qty_a, qty_b):
    """'kept' | 'lost' (dejó de coordinar) | 'new' (nuevo coordinado) | None."""
    billed_a, billed_b = not br.is_zero(qty_a), not br.is_zero(qty_b)
    if billed_a and billed_b:
        return 'kept'
    if billed_a:
        return 'lost'
    if billed_b:
        return 'new'
    return None


def aggregate(base, key_fn, labels_fn, sort_fn):
    """Agrupa los registros base por key_fn y suma los meses. Cada fila trae
    los clientes distintos que tuvo en cada temporada ('clients'), su estatus
    y el primer registro del grupo ('rec') para sacar metadatos. Descarta los
    grupos donde nada se coordinó en ninguna de las dos temporadas."""
    groups = {}
    for rec in base:
        g = groups.setdefault(key_fn(rec), {'rec': rec, 'months': zero_months(), 'partners': {}})
        for m in MONTHS_ORDER:
            g['months'][m][0] += rec['months'][m][0]
            g['months'][m][1] += rec['months'][m][1]
        qa, qb = totals(rec['months'])
        p = g['partners'].setdefault(rec['partner_id'], [0.0, 0.0])
        p[0] += qa
        p[1] += qb
    rows = []
    for g in groups.values():
        qa, qb = totals(g['months'])
        status = status_of(qa, qb)
        if not status:
            continue
        rows.append({
            'labels': labels_fn(g['rec']),
            'months': g['months'], 'qty_a': qa, 'qty_b': qb,
            'clients': (sum(1 for p in g['partners'].values() if not br.is_zero(p[0])),
                        sum(1 for p in g['partners'].values() if not br.is_zero(p[1]))),
            'status': status, 'rec': g['rec'],
        })
    rows.sort(key=lambda r: sort_fn(r['rec']))
    return rows


def sum_rows(rows):
    months = zero_months()
    for r in rows:
        for m in MONTHS_ORDER:
            months[m][0] += r['months'][m][0]
            months[m][1] += r['months'][m][1]
    qa, qb = totals(months)
    return months, qa, qb


def total_row(rows, label, n_labels, extra=None, clients=None):
    months, qa, qb = sum_rows(rows)
    return {'labels': [label] + [''] * (n_labels - 1), 'months': months, 'qty_a': qa, 'qty_b': qb,
            'clients': clients, 'extra': extra, 'is_total': True}


def build(base):
    """Arma todas las tablas del reporte a partir de los registros base."""
    def none_last(flag):
        return 1 if flag else 0

    coords = aggregate(
        base, lambda r: r['coord_id'] or False, lambda r: [r['coord_name']],
        lambda r: (none_last(not r['coord_id']), r['coord_name'].lower()))
    coord_schemes = aggregate(
        base, lambda r: (r['coord_id'] or False, r['scheme_id'] or False),
        lambda r: [r['coord_name'], r['scheme_name']],
        lambda r: (none_last(not r['coord_id']), r['coord_name'].lower(),
                   none_last(not r['scheme_id']), r.get('scheme_seq', 0), r['scheme_name'].lower()))
    clients = aggregate(
        base, lambda r: (r['scheme_id'] or False, r['partner_id']),
        lambda r: [r['partner_name'], r['group_name'], r['promotor_name']],
        lambda r: (none_last(not r['scheme_id']), r.get('scheme_seq', 0), r['scheme_name'].lower(),
                   r['partner_name'].lower()))

    # Clientes distintos en general (un cliente con dos coordinadores cuenta una vez).
    overall = {}
    for rec in base:
        qa, qb = totals(rec['months'])
        p = overall.setdefault(rec['partner_id'], [0.0, 0.0])
        p[0] += qa
        p[1] += qb
    overall_clients = (sum(1 for p in overall.values() if not br.is_zero(p[0])),
                       sum(1 for p in overall.values() if not br.is_zero(p[1])))

    # Bloques por esquema con sus clientes + resumen por esquema.
    blocks, order = {}, []
    for r in clients:
        key = r['rec']['scheme_id'] or False
        if key not in blocks:
            blocks[key] = {'name': r['rec']['scheme_name'], 'rows': []}
            order.append(key)
        blocks[key]['rows'].append(r)
    block_list = []
    for key in order:
        b = blocks[key]
        counts = {s: sum(1 for r in b['rows'] if r['status'] == s) for s in ('kept', 'lost', 'new')}
        counts['a'] = counts['kept'] + counts['lost']
        counts['b'] = counts['kept'] + counts['new']
        b['counts'] = counts
        b['total'] = total_row(b['rows'], 'Totales (%d clientes)' % len(b['rows']), 3)
        block_list.append(b)
    scheme_summary = []
    for b in block_list:
        row = total_row(b['rows'], b['name'], 1, extra=[b['counts']['a'], b['counts']['b'], b['counts']['lost'], b['counts']['new']])
        row['is_total'] = False
        scheme_summary.append(row)
    scheme_total = total_row(
        clients, 'Total general', 1,
        extra=[sum(b['counts']['a'] for b in block_list), sum(b['counts']['b'] for b in block_list),
               sum(b['counts']['lost'] for b in block_list), sum(b['counts']['new'] for b in block_list)])

    return {
        'coords': coords + [total_row(coords, 'Total general', 1, clients=overall_clients)],
        'coord_schemes': coord_schemes + [total_row(coord_schemes, 'Total general', 2, clients=overall_clients)],
        'scheme_summary': scheme_summary + [scheme_total],
        'blocks': block_list,
    }


# ----------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------

def _qty(value):
    value = value or 0.0
    return '{:,.0f}'.format(value) if abs(value - round(value)) < 1e-9 else '{:,.2f}'.format(value)


def _render_table(title, label_headers, rows, year_a, year_b, extra_headers=(), with_months=True, show_clients=True):
    label_a, label_b = br.season_label(year_a), br.season_label(year_b)
    has_clients = show_clients and any(r.get('clients') for r in rows)
    head1 = ''.join('<th rowspan="2">%s</th>' % br._esc(h) for h in label_headers)
    head1 += ''.join('<th rowspan="2">%s</th>' % br._esc(h) for h in extra_headers)
    head2 = ''
    if has_clients:
        head1 += '<th class="sc-sep" colspan="2">Clientes atendidos</th>'
        head2 += '<th class="sc-sep">%s</th><th>%s</th>' % (label_a, label_b)
    head1 += '<th class="sc-sep" colspan="3">Servicios coordinados</th>'
    head2 += '<th class="sc-sep">%s</th><th>%s</th><th>Var #</th>' % (label_a, label_b)
    if with_months:
        for mm, name in MONTHS:
            head1 += '<th class="sc-sep" colspan="3">%s</th>' % name
            head2 += '<th class="sc-sep">%d</th><th>%d</th><th>Var #</th>' % (
                br.month_year(year_a, mm), br.month_year(year_b, mm))

    body = ''
    for r in rows:
        cells = '<td>%s</td>' % br._esc(r['labels'][0])
        cells += ''.join('<td class="sc-l">%s</td>' % br._esc(x) for x in r['labels'][1:])
        if extra_headers:
            cells += ''.join('<td>%s</td>' % v for v in (r.get('extra') or [''] * len(extra_headers)))
        if has_clients:
            ca, cb = r['clients'] if r.get('clients') else ('', '')
            cells += '<td class="sc-sep">%s</td><td>%s</td>' % (ca, cb)
        cells += '<td class="sc-sep">%s</td><td>%s</td><td>%s</td>' % (
            _qty(r['qty_a']), _qty(r['qty_b']), br._var_html(r['qty_a'], r['qty_b']))
        if with_months:
            for m in MONTHS_ORDER:
                qa, qb = r['months'][m]
                cells += '<td class="sc-sep">%s</td><td>%s</td><td>%s</td>' % (_qty(qa), _qty(qb), br._var_html(qa, qb))
        body += '<tr%s>%s</tr>' % (' class="sc-total"' if r.get('is_total') else '', cells)

    return '''
    <div class="sc-block">
      <div class="sc-title">%s</div>
      <div class="sc-wrap"><table class="sc-table">
        <thead><tr>%s</tr><tr>%s</tr></thead>
        <tbody>%s</tbody>
      </table></div>
    </div>''' % (br._esc(title), head1, head2, body)


def _scheme_summary_headers(year_a, year_b):
    la, lb = br.season_label(year_a), br.season_label(year_b)
    return ['Clientes %s' % la, 'Clientes %s' % lb, 'Dejaron de coordinar', 'Nuevos coordinados']


def render_html(base, year_a, year_b):
    if not base:
        return ('<p>No hay servicios coordinados (compras confirmadas con pedido de venta, producto '
                'comisionable y fecha de servicio) en las temporadas elegidas.</p>')
    data = build(base)
    la, lb = br.season_label(year_a), br.season_label(year_b)
    out = br.CSS
    out += _render_table('Resumen por esquema — %s vs %s' % (la, lb), ['Esquema'], data['scheme_summary'], year_a, year_b,
                         extra_headers=_scheme_summary_headers(year_a, year_b), with_months=False)
    for b in data['blocks']:
        out += _render_table(b['name'], ['Cliente', 'Grupo', 'Promotor'], [b['total']] + b['rows'], year_a, year_b,
                             show_clients=False)
    out += _render_table('Coordinador y esquema', ['Coordinador', 'Esquema'], data['coord_schemes'], year_a, year_b)
    out += _render_table('Servicios por coordinador', ['Coordinador'], data['coords'], year_a, year_b)
    return out


# ----------------------------------------------------------------------
# Excel
# ----------------------------------------------------------------------

def render_xlsx(base, year_a, year_b):
    """Cuatro hojas: Resumen Esquema, Clientes (un bloque por esquema),
    Coordinador-Esquema y Coordinadores."""
    import xlsxwriter

    data = build(base) if base else {'coords': [], 'coord_schemes': [], 'scheme_summary': [], 'blocks': []}
    label_a, label_b = br.season_label(year_a), br.season_label(year_b)
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})
    teal = '#1B7F8C'
    f = {
        'title': wb.add_format({'bold': True, 'font_size': 14, 'font_color': teal}),
        'head': wb.add_format({'bold': True, 'bg_color': teal, 'font_color': 'white', 'border': 1,
                               'align': 'center', 'valign': 'vcenter', 'text_wrap': True}),
        'sub': wb.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1, 'align': 'center', 'text_wrap': True}),
        'txt': wb.add_format({'border': 1}),
        'txt_b': wb.add_format({'border': 1, 'bold': True, 'bg_color': '#EEF6F7'}),
        'num': wb.add_format({'border': 1, 'num_format': '#,##0.##'}),
        'num_b': wb.add_format({'border': 1, 'num_format': '#,##0.##', 'bold': True, 'bg_color': '#EEF6F7'}),
    }
    for kind, color in (('pos', '#2E7D32'), ('neg', '#C62828'), ('zero', '#F9A825')):
        for bold in (False, True):
            f['%s%s' % (kind, '_b' if bold else '')] = wb.add_format({
                'border': 1, 'num_format': '0.00%', 'font_color': color, 'bold': bold,
                **({'bg_color': '#EEF6F7'} if bold else {})})
    for bold in (False, True):
        f['new%s' % ('_b' if bold else '')] = wb.add_format({
            'border': 1, 'font_color': '#1F4E78', 'bg_color': '#BDD7EE', 'bold': bold, 'align': 'right'})

    def write_var(ws, r, c, a, b, bold):
        pct, kind = br.variation(a, b)
        suffix = '_b' if bold else ''
        if kind == 'new':
            ws.write_string(r, c, 'Nuevo', f['new' + suffix])
        else:
            cls = 'neg' if pct < -0.00005 else ('pos' if pct > 0.00005 else 'zero')
            ws.write_number(r, c, pct, f[cls + suffix])

    def write_table(ws, r, title, label_headers, rows, extra_headers=(), with_months=True, show_clients=True):
        has_clients = show_clients and any(x.get('clients') for x in rows)
        n_lab, n_extra = len(label_headers), len(extra_headers)
        ws.write(r, 0, title, f['title'])
        r += 1
        c = 0
        for h in list(label_headers) + list(extra_headers):
            ws.merge_range(r, c, r + 1, c, h, f['head'])
            c += 1
        if has_clients:
            ws.merge_range(r, c, r, c + 1, 'Clientes atendidos', f['head'])
            ws.write(r + 1, c, label_a, f['sub'])
            ws.write(r + 1, c + 1, label_b, f['sub'])
            c += 2
        ws.merge_range(r, c, r, c + 2, 'Servicios coordinados', f['head'])
        for i, t in enumerate((label_a, label_b, 'Var #')):
            ws.write(r + 1, c + i, t, f['sub'])
        c += 3
        if with_months:
            for mm, name in MONTHS:
                ws.merge_range(r, c, r, c + 2, name, f['head'])
                for i, t in enumerate((str(br.month_year(year_a, mm)), str(br.month_year(year_b, mm)), 'Var #')):
                    ws.write(r + 1, c + i, t, f['sub'])
                c += 3
        r += 2
        for row in rows:
            bold = bool(row.get('is_total'))
            lf, nf = f['txt_b' if bold else 'txt'], f['num_b' if bold else 'num']
            c = 0
            for label in row['labels']:
                ws.write(r, c, label or '', lf)
                c += 1
            for v in (row.get('extra') or [''] * n_extra)[:n_extra]:
                ws.write(r, c, v, nf)
                c += 1
            if has_clients:
                ca, cb = row['clients'] if row.get('clients') else ('', '')
                ws.write(r, c, ca, nf)
                ws.write(r, c + 1, cb, nf)
                c += 2
            ws.write_number(r, c, row['qty_a'], nf)
            ws.write_number(r, c + 1, row['qty_b'], nf)
            write_var(ws, r, c + 2, row['qty_a'], row['qty_b'], bold)
            c += 3
            if with_months:
                for m in MONTHS_ORDER:
                    qa, qb = row['months'][m]
                    ws.write_number(r, c, qa, nf)
                    ws.write_number(r, c + 1, qb, nf)
                    write_var(ws, r, c + 2, qa, qb, bold)
                    c += 3
            r += 1
        return r + 1

    def sheet(name, first_width):
        ws = wb.add_worksheet(name)
        ws.set_column(0, 0, first_width)
        ws.set_column(1, 2, 22)
        ws.set_column(3, 60, 12)
        ws.freeze_panes(0, 1)
        return ws

    write_table(sheet('Resumen Esquema', 30), 0, 'Resumen por esquema', ['Esquema'], data['scheme_summary'],
                extra_headers=_scheme_summary_headers(year_a, year_b), with_months=False)
    ws = sheet('Clientes', 40)
    r = 0
    for b in data['blocks']:
        r = write_table(ws, r, b['name'], ['Cliente', 'Grupo', 'Promotor'], [b['total']] + b['rows'], show_clients=False)
    write_table(sheet('Coordinador-Esquema', 34), 0, 'Coordinador y esquema', ['Coordinador', 'Esquema'], data['coord_schemes'])
    write_table(sheet('Coordinadores', 34), 0, 'Servicios por coordinador', ['Coordinador'], data['coords'])
    wb.close()
    return output.getvalue()
