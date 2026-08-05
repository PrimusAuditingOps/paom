# -*- coding: utf-8 -*-
import base64
import json
import math
import xml.etree.ElementTree as ET

from odoo import api, fields, models, _

EARTH_RADIUS_M = 6378137.0
KML_NS = 'http://www.opengis.net/kml/2.2'

# KML colors are aabbggrr (alpha, blue, green, red). One style per site state
# so Calidad can tell sites apart by color at a glance in Google Earth, on
# top of the name/area tooltip.
KML_STYLE_BY_STATE = {
    'draft': 'pao_site_plot_style_draft',
    'sent_to_calidad': 'pao_site_plot_style_sent_to_calidad',
    'reviewed': 'pao_site_plot_style_reviewed',
}
KML_STYLE_COLORS = {
    'pao_site_plot_style_draft': ('ff0000ff', '4d0000ff'),            # red
    'pao_site_plot_style_sent_to_calidad': ('ffff0000', '4dff0000'),  # blue
    'pao_site_plot_style_reviewed': ('ff00ff00', '4d00ff00'),         # green
}


def _polar_triangle_area(tan_lat1, lng1, tan_lat2, lng2):
    """Signed area of the polar triangle for two consecutive ring vertices.

    Same algorithm as Google Maps' SphericalUtil.computeArea (spherical.js),
    kept here so the server-authoritative area matches what the map widget
    shows live while a polygon is being edited.
    """
    delta_lng = lng1 - lng2
    t = tan_lat1 * tan_lat2
    return 2 * math.atan2(t * math.sin(delta_lng), 1 + t * math.cos(delta_lng))


def compute_geodesic_area_m2(ring):
    """Area in square meters of a closed [lng, lat] ring on a sphere."""
    if len(ring) < 4:  # a closed ring needs at least 3 distinct points + closing point
        return 0.0
    total = 0.0
    prev_lng, prev_lat = ring[-1][0], ring[-1][1]
    prev_tan_lat = math.tan((math.pi / 2 - math.radians(prev_lat)) / 2)
    prev_lng_rad = math.radians(prev_lng)
    for lng, lat in ring:
        tan_lat = math.tan((math.pi / 2 - math.radians(lat)) / 2)
        lng_rad = math.radians(lng)
        total += _polar_triangle_area(tan_lat, lng_rad, prev_tan_lat, prev_lng_rad)
        prev_tan_lat = tan_lat
        prev_lng_rad = lng_rad
    return abs(total) * EARTH_RADIUS_M * EARTH_RADIUS_M


class PaoSitePlot(models.Model):
    _name = 'pao.site.plot'
    _description = 'Site / Plot Polygon'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Cotización',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(string='Sitio', required=True, tracking=True)
    partner_owner_name = fields.Char(string='Propietario')
    variety = fields.Char(string='Frutos')
    location = fields.Char(string='Ubicación')
    declared_surface_ha = fields.Float(string='Superficie declarada (HA)', digits=(12, 4))
    computed_surface_ha = fields.Float(
        string='Superficie calculada (HA)',
        digits=(12, 4),
        readonly=True,
        copy=False,
    )
    surface_variance_pct = fields.Float(
        string='Variación vs. declarada (%)',
        compute='_compute_surface_variance',
        store=True,
        digits=(12, 2),
    )
    center_lat = fields.Float(string='Latitud', digits=(10, 7))
    center_lng = fields.Float(string='Longitud', digits=(10, 7))
    geojson_polygon = fields.Text(string='Polígono (GeoJSON)', copy=False)
    source = fields.Selection(
        selection=[
            ('manual', 'Dibujado manualmente'),
            ('kml_import', 'Importado de KML'),
            ('excel_import', 'Importado de Excel'),
        ],
        string='Origen',
        default='manual',
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('sent_to_calidad', 'Enviado a Calidad'),
            ('reviewed', 'Revisado por Calidad'),
        ],
        string='Estado',
        default='draft',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='sale_order_id.company_id',
        store=True,
    )

    @api.depends('declared_surface_ha', 'computed_surface_ha')
    def _compute_surface_variance(self):
        for site in self:
            if site.declared_surface_ha:
                site.surface_variance_pct = (
                    (site.computed_surface_ha - site.declared_surface_ha)
                    / site.declared_surface_ha * 100
                )
            else:
                site.surface_variance_pct = 0.0

    def _recompute_area_from_geojson(self):
        for site in self:
            if not site.geojson_polygon:
                site.computed_surface_ha = 0.0
                continue
            try:
                geo = json.loads(site.geojson_polygon)
                ring = geo['coordinates'][0]
            except (ValueError, KeyError, IndexError, TypeError):
                site.computed_surface_ha = 0.0
                continue
            area_m2 = compute_geodesic_area_m2(ring)
            site.computed_surface_ha = area_m2 / 10000.0

    @api.model_create_multi
    def create(self, vals_list):
        sites = super().create(vals_list)
        sites._recompute_area_from_geojson()
        return sites

    def write(self, vals):
        res = super().write(vals)
        if 'geojson_polygon' in vals:
            self._recompute_area_from_geojson()
        return res

    def _kml_description(self):
        self.ensure_one()
        state_labels = dict(self._fields['state'].selection)
        lines = []
        if self.partner_owner_name:
            lines.append(_('Propietario: %s') % self.partner_owner_name)
        if self.variety:
            lines.append(_('Frutos: %s') % self.variety)
        if self.location:
            lines.append(_('Ubicación: %s') % self.location)
        lines.append(_('Superficie declarada: %.4f ha') % self.declared_surface_ha)
        lines.append(_('Superficie calculada: %.4f ha') % self.computed_surface_ha)
        lines.append(_('Estado: %s') % state_labels.get(self.state, self.state))
        return '<br/>'.join(lines)

    @staticmethod
    def _add_kml_styles(doc):
        for style_id, (line_color, poly_color) in KML_STYLE_COLORS.items():
            style = ET.SubElement(doc, 'Style', id=style_id)
            line_style = ET.SubElement(style, 'LineStyle')
            ET.SubElement(line_style, 'color').text = line_color
            ET.SubElement(line_style, 'width').text = '2'
            poly_style = ET.SubElement(style, 'PolyStyle')
            ET.SubElement(poly_style, 'color').text = poly_color

    def action_export_kml(self):
        """Export the selected sites (or all of a single order's sites) as one .kml
        Document, attached to the related sale.order chatter."""
        sites = self.filtered('geojson_polygon')
        if not sites:
            return False
        root = ET.Element('kml', xmlns=KML_NS)
        doc = ET.SubElement(root, 'Document')
        self._add_kml_styles(doc)
        for site in sites:
            placemark = ET.SubElement(doc, 'Placemark')
            ET.SubElement(placemark, 'name').text = site.name
            ET.SubElement(placemark, 'description').text = site._kml_description()
            ET.SubElement(placemark, 'styleUrl').text = '#%s' % KML_STYLE_BY_STATE.get(
                site.state, KML_STYLE_BY_STATE['draft']
            )
            geo = json.loads(site.geojson_polygon)
            polygon = ET.SubElement(placemark, 'Polygon')
            outer = ET.SubElement(polygon, 'outerBoundaryIs')
            ring_el = ET.SubElement(outer, 'LinearRing')
            coords_text = ' '.join(
                '%s,%s,0' % (lng, lat) for lng, lat in geo['coordinates'][0]
            )
            ET.SubElement(ring_el, 'coordinates').text = coords_text
        xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)

        order = sites[0].sale_order_id
        attachment = self.env['ir.attachment'].create({
            'name': '%s.kml' % (order.name or 'sitios'),
            'type': 'binary',
            'datas': base64.b64encode(xml_bytes),
            'res_model': 'sale.order',
            'res_id': order.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
