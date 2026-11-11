"""Lógica pura (sin ORM) del comparativo de facturación por temporada: arma
los bloques por esquema, calcula variaciones y renderiza HTML / Excel.

Se mantiene separada del wizard para poder probarla sin una base de Odoo.

Cada "fila" es un dict con una combinación (esquema, cliente):
    scheme_id, scheme_name, scheme_seq, partner_id, partner_name, group_name,
    promotor_name, months {'09': [cant_A, usd_A, cant_B, usd_B], ...},
    qty_a, amt_a, qty_b, amt_b, status ('kept' | 'lost' | 'new')
"""
import calendar
import html
import io
from datetime import date

MONTHS = [
    ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
    ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
    ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
]
MONTHS_ORDER = [m for m, _n in MONTHS]
MONTH_SHORT = {
    '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic', '01': 'Ene', '02': 'Feb',
    '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago',
}
EPS = 0.005


# ----------------------------------------------------------------------
# Temporadas
# ----------------------------------------------------------------------

def month_year(season_year, mm):
    """Año calendario de un mes dentro de la temporada (sep-dic = year, ene-ago = year+1)."""
    return season_year if int(mm) >= 9 else season_year + 1


def season_dates(year, cutoff=None):
    """Una temporada va del 1 de septiembre de `year` al 31 de agosto de year+1.
    Con `cutoff` (un mes '09'..'08'), termina el último día de ese mes."""
    if not cutoff:
        return date(year, 9, 1), date(year + 1, 8, 31)
    y = month_year(year, cutoff)
    return date(year, 9, 1), date(y, int(cutoff), calendar.monthrange(y, int(cutoff))[1])


def months_upto(cutoff=None):
    """Meses (código, nombre) de la temporada, de septiembre hasta `cutoff`
    (todos si no hay corte)."""
    if not cutoff:
        return list(MONTHS)
    return MONTHS[:MONTHS_ORDER.index(cutoff) + 1]


def cutoff_name(cutoff):
    return dict(MONTHS).get(cutoff, '')


def season_label(year):
    return 'Temp.%02d-%02d' % (year % 100, (year + 1) % 100)


# ----------------------------------------------------------------------
# Cálculos
# ----------------------------------------------------------------------

def is_zero(value):
    return abs(value or 0.0) < EPS


def variation(a, b):
    """Variación de b contra la base a. Regresa (fracción, tipo) con tipo:
    'pct' (normal), 'zero' (ambos en 0) o 'new' (base en 0 y sí hubo en b: no
    hay porcentaje calculable, es un cliente nuevo o recuperado)."""
    if is_zero(a):
        return (0.0, 'zero' if is_zero(b) else 'new')
    return ((b - a) / abs(a), 'pct')


def status_of(qty_a, amt_a, qty_b, amt_b):
    billed_a = not (is_zero(qty_a) and is_zero(amt_a))
    billed_b = not (is_zero(qty_b) and is_zero(amt_b))
    if billed_a and billed_b:
        return 'kept'
    if billed_a:
        return 'lost'
    if billed_b:
        return 'new'
    return None


def sum_rows(rows):
    months = {m: [0.0, 0.0, 0.0, 0.0] for m in MONTHS_ORDER}
    for r in rows:
        for m in MONTHS_ORDER:
            for i in range(4):
                months[m][i] += r['months'][m][i]
    return {
        'months': months,
        'qty_a': sum(r['qty_a'] for r in rows),
        'amt_a': sum(r['amt_a'] for r in rows),
        'qty_b': sum(r['qty_b'] for r in rows),
        'amt_b': sum(r['amt_b'] for r in rows),
    }


def count_status(rows):
    c = {'kept': 0, 'lost': 0, 'new': 0}
    for r in rows:
        c[r['status']] += 1
    c['a'] = c['kept'] + c['lost']
    c['b'] = c['kept'] + c['new']
    return c


def build_blocks(rows):
    """Agrupa las filas (ya ordenadas por esquema y cliente) en un bloque por
    esquema, con sus totales y conteo de clientes."""
    blocks, order = {}, []
    for r in rows:
        key = r['scheme_id'] or False
        if key not in blocks:
            blocks[key] = {'scheme_id': key, 'name': r['scheme_name'], 'rows': []}
            order.append(key)
        blocks[key]['rows'].append(r)
    result = []
    for key in order:
        b = blocks[key]
        b['totals'] = sum_rows(b['rows'])
        b['counts'] = count_status(b['rows'])
        result.append(b)
    return result


# ----------------------------------------------------------------------
# HTML (vista en pantalla)
# ----------------------------------------------------------------------

CSS = '''<style>
    .sc-block{margin-bottom:26px;}
    .sc-title{color:#1B7F8C;font-weight:bold;font-size:18px;margin:6px 0;}
    .sc-wrap{overflow-x:auto;max-height:75vh;}
    .sc-table{border-collapse:separate;border-spacing:0;font-size:12px;}
    .sc-table th, .sc-table td{border-bottom:1px solid #e3e3e3;border-right:1px solid #f0f0f0;padding:3px 8px;text-align:right;white-space:nowrap;background:#fff;}
    .sc-table th{background:#f5f5f5;text-align:center;color:#1B7F8C;position:sticky;top:0;z-index:2;}
    .sc-table td:first-child, .sc-table th:first-child{text-align:left;position:sticky;left:0;z-index:3;border-right:2px solid #ccc;}
    .sc-table th:first-child{z-index:4;}
    .sc-table td.sc-l{text-align:left;}
    .sc-total td{font-weight:bold;background:#eef6f7;border-bottom:2px solid #1B7F8C;}
    .sc-sep{border-left:2px solid #bbb !important;}
    .sc-pos{color:#2E7D32;} .sc-neg{color:#C62828;} .sc-zero{color:#F9A825;}
    .sc-new{color:#1F4E78;background:#BDD7EE;padding:0 5px;border-radius:3px;}
</style>'''


def _num(value):
    return '{:,.2f}'.format(value or 0.0)


def _esc(value):
    return html.escape(value or '', quote=True)


def _var_html(a, b):
    pct, kind = variation(a, b)
    if kind == 'new':
        return '<span class="sc-new">Nuevo</span>'
    cls = 'sc-neg' if pct < -0.00005 else ('sc-pos' if pct > 0.00005 else 'sc-zero')
    return '<span class="%s">%.2f%%</span>' % (cls, pct * 100)


def _summary_cells(data, counts=None):
    cells = ''
    if counts is not None:
        cells += '<td>%d</td><td>%d</td><td>%d</td><td>%d</td>' % (
            counts['a'], counts['b'], counts['lost'], counts['new'])
    cells += '<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (
        _num(data['qty_a']), _num(data['amt_a']), _num(data['qty_b']), _num(data['amt_b']),
        _var_html(data['qty_a'], data['qty_b']), _var_html(data['amt_a'], data['amt_b']))
    return cells


def _render_summary(blocks, grand, grand_counts, label_a, label_b, suffix=''):
    body = ''
    for b in blocks:
        body += '<tr><td>%s</td>%s</tr>' % (_esc(b['name']), _summary_cells(b['totals'], b['counts']))
    body += '<tr class="sc-total"><td>Total general</td>%s</tr>' % _summary_cells(grand, grand_counts)
    return '''
    <div class="sc-block">
      <div class="sc-title">Resumen por esquema — %s vs %s%s</div>
      <div class="sc-wrap"><table class="sc-table">
        <thead>
          <tr>
            <th rowspan="2">Esquema</th>
            <th colspan="4">Clientes que facturaron</th>
            <th colspan="2">%s</th><th colspan="2">%s</th><th colspan="2">Variación</th>
          </tr>
          <tr>
            <th>%s</th><th>%s</th><th>Dejaron de facturar</th><th>Nuevos facturados</th>
            <th>#</th><th>USD</th><th>#</th><th>USD</th><th>Var #</th><th>Var $</th>
          </tr>
        </thead>
        <tbody>%s</tbody>
      </table></div>
    </div>''' % (label_a, label_b, suffix, label_a, label_b, label_a, label_b, body)


def _labels_of(row):
    """Textos de las columnas de etiqueta: los que traiga la fila o, si es un
    cliente, su nombre, grupo y promotor."""
    return row.get('labels') or [row['partner_name'], row['group_name'], row['promotor_name']]


def _row_cells(row, label_cells, months):
    cells = label_cells
    cells += '<td class="sc-sep">%s</td><td>%s</td><td class="sc-sep">%s</td><td>%s</td><td class="sc-sep">%s</td><td>%s</td>' % (
        _num(row['qty_a']), _num(row['amt_a']), _num(row['qty_b']), _num(row['amt_b']),
        _var_html(row['qty_a'], row['qty_b']), _var_html(row['amt_a'], row['amt_b']))
    for m, _name in months:
        qa, aa, qb, ab = row['months'][m]
        cells += (
            '<td class="sc-sep">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
        ) % (_num(qa), _num(aa), _num(qb), _num(ab), _var_html(qa, qb), _var_html(aa, ab))
    return cells


def _render_detail(title, label_headers, rows, year_a, year_b, months):
    label_a, label_b = season_label(year_a), season_label(year_b)
    month_headers, month_sub = '', ''
    for mm, name in months:
        ya, yb = month_year(year_a, mm), month_year(year_b, mm)
        month_headers += '<th class="sc-sep" colspan="6">%s</th>' % name
        month_sub += (
            '<th class="sc-sep">Cant. %d</th><th>USD %d</th><th>Cant. %d</th><th>USD %d</th>'
            '<th>Var Cant.</th><th>Var $</th>'
        ) % (ya, ya, yb, yb)

    body = ''
    for r in rows:
        labels = _labels_of(r)
        label_cells = '<td>%s</td>' % _esc(labels[0]) + ''.join(
            '<td class="sc-l">%s</td>' % _esc(x) for x in labels[1:])
        body += '<tr%s>%s</tr>' % (' class="sc-total"' if r.get('is_total') else '', _row_cells(r, label_cells, months))

    head = ''.join('<th rowspan="2">%s</th>' % _esc(h) for h in label_headers)
    return '''
    <div class="sc-block">
      <div class="sc-title">%s</div>
      <div class="sc-wrap"><table class="sc-table">
        <thead>
          <tr>
            %s
            <th class="sc-sep" colspan="2">%s</th><th class="sc-sep" colspan="2">%s</th><th class="sc-sep" colspan="2">Variación</th>
            %s
          </tr>
          <tr>
            <th class="sc-sep">#</th><th>USD</th><th class="sc-sep">#</th><th>USD</th>
            <th class="sc-sep">Var #</th><th>Var $</th>
            %s
          </tr>
        </thead>
        <tbody>%s</tbody>
      </table></div>
    </div>''' % (_esc(title), head, label_a, label_b, month_headers, month_sub, body)


def _scheme_month_rows(blocks, grand):
    """Un renglón por esquema (con sus meses) más el Total general."""
    rows = [dict(b['totals'], labels=[b['name']]) for b in blocks]
    rows.append(dict(grand, labels=['Total general'], is_total=True))
    return rows


def _client_rows(block):
    total = dict(block['totals'], labels=['Totales (%d clientes)' % len(block['rows']), '', ''], is_total=True)
    return [total] + block['rows']


def render_html(rows, year_a, year_b, cutoff=None):
    if not rows:
        return '<p>No hay facturación de productos comisionables en las temporadas elegidas.</p>'
    blocks = build_blocks(rows)
    grand = sum_rows(rows)
    grand_counts = count_status(rows)
    months = months_upto(cutoff)
    suffix = ' (hasta %s)' % cutoff_name(cutoff) if cutoff else ''
    out = CSS + _render_summary(blocks, grand, grand_counts, season_label(year_a), season_label(year_b), suffix)
    out += _render_detail('Resumen por mes y esquema%s' % suffix, ['Esquema'], _scheme_month_rows(blocks, grand),
                          year_a, year_b, months)
    for b in blocks:
        out += _render_detail(b['name'], ['Cliente', 'Grupo', 'Promotor'], _client_rows(b), year_a, year_b, months)
    return out


# ----------------------------------------------------------------------
# Excel
# ----------------------------------------------------------------------

def render_xlsx(rows, year_a, year_b, cutoff=None):
    """Regresa los bytes de un .xlsx con tres hojas: 'Resumen' (un renglón por
    esquema), 'Resumen Mes-Esquema' (esquemas con detalle por mes) y
    'Comparativo' (un bloque por esquema, con sus clientes)."""
    import xlsxwriter

    label_a, label_b = season_label(year_a), season_label(year_b)
    blocks = build_blocks(rows)
    grand = sum_rows(rows)
    grand_counts = count_status(rows) if rows else {'a': 0, 'b': 0, 'lost': 0, 'new': 0, 'kept': 0}
    months = months_upto(cutoff)

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
        'num': wb.add_format({'border': 1, 'num_format': '#,##0.00'}),
        'num_b': wb.add_format({'border': 1, 'num_format': '#,##0.00', 'bold': True, 'bg_color': '#EEF6F7'}),
        'int': wb.add_format({'border': 1, 'num_format': '0'}),
        'int_b': wb.add_format({'border': 1, 'num_format': '0', 'bold': True, 'bg_color': '#EEF6F7'}),
    }
    for kind, color in (('pos', '#2E7D32'), ('neg', '#C62828'), ('zero', '#F9A825')):
        for bold in (False, True):
            f['%s%s' % (kind, '_b' if bold else '')] = wb.add_format({
                'border': 1, 'num_format': '0.00%', 'font_color': color, 'bold': bold,
                **({'bg_color': '#EEF6F7'} if bold else {})})
    for bold in (False, True):
        f['new%s' % ('_b' if bold else '')] = wb.add_format({
            'border': 1, 'font_color': '#1F4E78', 'bg_color': '#BDD7EE', 'bold': bold, 'align': 'right'})

    def write_var(ws, r, c, a, b, bold=False):
        pct, kind = variation(a, b)
        suffix = '_b' if bold else ''
        if kind == 'new':
            ws.write_string(r, c, 'Nuevo', f['new' + suffix])
            return
        cls = 'neg' if pct < -0.00005 else ('pos' if pct > 0.00005 else 'zero')
        ws.write_number(r, c, pct, f[cls + suffix])

    # --- Hoja Resumen ---
    ws = wb.add_worksheet('Resumen')
    ws.merge_range(0, 0, 1, 0, 'Esquema', f['head'])
    ws.merge_range(0, 1, 0, 4, 'Clientes que facturaron', f['head'])
    ws.merge_range(0, 5, 0, 6, label_a, f['head'])
    ws.merge_range(0, 7, 0, 8, label_b, f['head'])
    ws.merge_range(0, 9, 0, 10, 'Variación', f['head'])
    for i, t in enumerate((label_a, label_b, 'Dejaron de facturar', 'Nuevos facturados', '#', 'USD', '#', 'USD', 'Var #', 'Var $')):
        ws.write(1, 1 + i, t, f['sub'])
    ws.set_column(0, 0, 30)
    ws.set_column(1, 10, 14)
    ws.freeze_panes(2, 1)
    r = 2
    for b in blocks + [{'name': 'Total general', 'totals': grand, 'counts': grand_counts, 'is_total': True}]:
        bold = b.get('is_total', False)
        ws.write(r, 0, b['name'], f['txt_b' if bold else 'txt'])
        c = b['counts']
        for i, v in enumerate((c['a'], c['b'], c['lost'], c['new'])):
            ws.write_number(r, 1 + i, v, f['int_b' if bold else 'int'])
        t = b['totals']
        for i, v in enumerate((t['qty_a'], t['amt_a'], t['qty_b'], t['amt_b'])):
            ws.write_number(r, 5 + i, v, f['num_b' if bold else 'num'])
        write_var(ws, r, 9, t['qty_a'], t['qty_b'], bold)
        write_var(ws, r, 10, t['amt_a'], t['amt_b'], bold)
        r += 1

    # --- Tablas con detalle por mes (resumen por mes y esquema / clientes de un esquema) ---
    def write_detail(ws, r, title, label_headers, detail_rows):
        n = len(label_headers)
        ws.write(r, 0, title, f['title'])
        r += 1
        for i, h in enumerate(label_headers):
            ws.merge_range(r, i, r + 1, i, h, f['head'])
        ws.merge_range(r, n, r, n + 1, label_a, f['head'])
        ws.merge_range(r, n + 2, r, n + 3, label_b, f['head'])
        ws.merge_range(r, n + 4, r, n + 5, 'Variación', f['head'])
        for i, t in enumerate(('#', 'USD', '#', 'USD', 'Var #', 'Var $')):
            ws.write(r + 1, n + i, t, f['sub'])
        col = n + 6
        for mm, name in months:
            ya, yb = month_year(year_a, mm), month_year(year_b, mm)
            ws.merge_range(r, col, r, col + 5, name, f['head'])
            for i, t in enumerate(('Cant. %d' % ya, 'USD %d' % ya, 'Cant. %d' % yb, 'USD %d' % yb, 'Var Cant.', 'Var $')):
                ws.write(r + 1, col + i, t, f['sub'])
            col += 6
        r += 2
        for row in detail_rows:
            bold = bool(row.get('is_total'))
            nf = f['num_b' if bold else 'num']
            for i, label in enumerate(_labels_of(row)):
                ws.write(r, i, label or '', f['txt_b' if bold else 'txt'])
            ws.write_number(r, n, row['qty_a'], nf)
            ws.write_number(r, n + 1, row['amt_a'], nf)
            ws.write_number(r, n + 2, row['qty_b'], nf)
            ws.write_number(r, n + 3, row['amt_b'], nf)
            write_var(ws, r, n + 4, row['qty_a'], row['qty_b'], bold)
            write_var(ws, r, n + 5, row['amt_a'], row['amt_b'], bold)
            col = n + 6
            for m, _name in months:
                qa, aa, qb, ab = row['months'][m]
                ws.write_number(r, col, qa, nf)
                ws.write_number(r, col + 1, aa, nf)
                ws.write_number(r, col + 2, qb, nf)
                ws.write_number(r, col + 3, ab, nf)
                write_var(ws, r, col + 4, qa, qb, bold)
                write_var(ws, r, col + 5, aa, ab, bold)
                col += 6
            r += 1
        return r + 1

    suffix = ' (hasta %s)' % cutoff_name(cutoff) if cutoff else ''
    ws = wb.add_worksheet('Resumen Mes-Esquema')
    ws.set_column(0, 0, 30)
    ws.set_column(1, 6 + 6 * 12, 12)
    ws.freeze_panes(0, 1)
    write_detail(ws, 0, 'Resumen por mes y esquema%s' % suffix, ['Esquema'], _scheme_month_rows(blocks, grand))

    ws = wb.add_worksheet('Comparativo')
    ws.set_column(0, 0, 40)
    ws.set_column(1, 2, 22)
    ws.set_column(3, 9 + 6 * 12, 12)
    ws.freeze_panes(0, 1)
    r = 0
    for b in blocks:
        r = write_detail(ws, r, b['name'], ['Cliente', 'Grupo', 'Promotor'], _client_rows(b))

    wb.close()
    return output.getvalue()
