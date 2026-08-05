/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onWillStart, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { loadGoogleMapsApi } from "./pao_google_maps_loader";

/**
 * Manual click-to-draw polygon tool. Google removed the Drawing library
 * (DrawingManager/OverlayType) from the Maps JS API as of v3.65, so vertices
 * are collected from map clicks into a Polyline preview and converted into an
 * editable Polygon once the user closes the ring.
 */
export class PaoPolygonMapField extends Component {
    static template = "pao_site_plot_survey.PolygonMapField";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.mapContainerRef = useRef("mapContainer");
        this.state = useState({ areaHa: 0, error: null, drawing: false, canFinish: false, hasPolygon: false });
        this.map = null;
        this.polygon = null;
        this.centerMarker = null;
        this.siblingOverlays = [];
        this.tempPoints = [];
        this.tempPolyline = null;
        this.mapClickListener = null;

        onWillStart(async () => {
            const apiKey = await this.orm.call("ir.config_parameter", "get_pao_google_maps_api_key", []);
            if (!apiKey) {
                this.state.error = "Configure la API key de Google Maps en Ajustes.";
                return;
            }
            try {
                await loadGoogleMapsApi(apiKey);
            } catch {
                this.state.error = "No se pudo cargar Google Maps.";
            }
        });
        // Re-runs whenever the pager/breadcrumb switches to a different
        // record: the component instance is reused across records (Odoo
        // doesn't remount field widgets on navigation), so without this the
        // map kept showing the previous site's polygon until a full reload.
        useEffect(
            () => {
                if (this.state.error) {
                    return;
                }
                this.cancelDrawing();
                if (!this.map) {
                    this._ensureMap();
                }
                this._renderRecord();
                this._loadSiblingSites();
            },
            () => [this.props.record.resId, this._saleOrderId()]
        );
        onWillUnmount(() => {
            this._removeClickListener();
            this._clearSiblingOverlays();
        });
    }

    get _rawValue() {
        return this.props.record.data[this.props.name];
    }

    _saleOrderId() {
        const value = this.props.record.data.sale_order_id;
        if (!value) {
            return false;
        }
        if (Array.isArray(value)) {
            return value[0];
        }
        return value.id !== undefined ? value.id : value;
    }

    /** Draws the other already-drawn sites of the same quotation as
     * non-editable, dimmed reference overlays, so the person drawing this
     * site's polygon can see where neighboring sites already are and avoid
     * overlapping their surfaces. */
    async _loadSiblingSites() {
        this._clearSiblingOverlays();
        const saleOrderId = this._saleOrderId();
        if (!saleOrderId || !this.map) {
            return;
        }
        const domain = [
            ["sale_order_id", "=", saleOrderId],
            ["geojson_polygon", "!=", false],
        ];
        if (this.props.record.resId) {
            domain.push(["id", "!=", this.props.record.resId]);
        }
        const siblings = await this.orm.searchRead("pao.site.plot", domain, ["name", "geojson_polygon"]);
        for (const sibling of siblings) {
            let geo;
            try {
                geo = JSON.parse(sibling.geojson_polygon);
            } catch {
                continue;
            }
            const path = geo.coordinates[0].map(([lng, lat]) => ({ lat, lng }));
            const polygon = new google.maps.Polygon({
                paths: path,
                map: this.map,
                clickable: false,
                editable: false,
                strokeColor: "#ff0000",
                fillColor: "#ff0000",
                fillOpacity: 0.25,
                strokeWeight: 2,
            });
            const marker = new google.maps.Marker({
                position: this._centroid(path),
                map: this.map,
                clickable: false,
                label: { text: sibling.name, color: "#ffffff", fontWeight: "bold", fontSize: "12px" },
                icon: { path: google.maps.SymbolPath.CIRCLE, scale: 0 },
            });
            this.siblingOverlays.push(polygon, marker);
        }
    }

    _clearSiblingOverlays() {
        this.siblingOverlays.forEach((overlay) => overlay.setMap(null));
        this.siblingOverlays = [];
    }

    _ensureMap() {
        this.map = new google.maps.Map(this.mapContainerRef.el, {
            mapTypeId: "satellite",
        });
    }

    _renderRecord() {
        const record = this.props.record;
        const raw = this._rawValue;
        let geojson = null;
        if (raw) {
            try {
                geojson = JSON.parse(raw);
            } catch {
                geojson = null;
            }
        }

        if (this.polygon) {
            this.polygon.setMap(null);
            this.polygon = null;
        }
        if (this.centerMarker) {
            this.centerMarker.setMap(null);
            this.centerMarker = null;
        }
        this.state.areaHa = 0;
        this.state.hasPolygon = false;

        const center = geojson
            ? this._centroid(geojson.coordinates[0])
            : {
                  lat: record.data.center_lat || 23.6,
                  lng: record.data.center_lng || -102.5,
              };
        this.map.setCenter(center);
        this.map.setZoom(geojson ? 16 : (record.data.center_lat ? 15 : 5));

        if (record.data.center_lat && record.data.center_lng) {
            this.centerMarker = new google.maps.Marker({
                position: { lat: record.data.center_lat, lng: record.data.center_lng },
                map: this.map,
                title: "Ubicación reportada por el cliente",
            });
        }

        if (geojson) {
            this.polygon = new google.maps.Polygon({
                paths: geojson.coordinates[0].map(([lng, lat]) => ({ lat, lng })),
                editable: !this.props.readonly,
                map: this.map,
            });
            this._bindPolygonEvents(this.polygon);
            this._updateAreaPreview(this.polygon);
            this.state.hasPolygon = true;
        }
    }

    startDrawing() {
        if (this.props.readonly) {
            return;
        }
        // The previous polygon (if any) is left untouched on the map until
        // finishDrawing() actually replaces it, so cancelling never loses data.
        this.tempPoints = [];
        this.tempPolyline = new google.maps.Polyline({
            map: this.map,
            path: [],
            strokeColor: "#1a73e8",
        });
        this.state.drawing = true;
        this.state.canFinish = false;
        this.mapClickListener = google.maps.event.addListener(this.map, "click", (ev) =>
            this._onMapClickWhileDrawing(ev)
        );
    }

    _onMapClickWhileDrawing(ev) {
        this.tempPoints.push(ev.latLng);
        this.tempPolyline.setPath(this.tempPoints);
        this.state.canFinish = this.tempPoints.length >= 3;
    }

    finishDrawing() {
        if (!this.state.canFinish) {
            return;
        }
        const points = this.tempPoints;
        this._removeClickListener();
        this.tempPolyline.setMap(null);
        this.tempPolyline = null;
        this.state.drawing = false;

        if (this.polygon) {
            this.polygon.setMap(null);
        }
        this.polygon = new google.maps.Polygon({
            paths: points,
            editable: !this.props.readonly,
            map: this.map,
            fillOpacity: 0.15,
        });
        this._bindPolygonEvents(this.polygon);
        this._commit(this.polygon);
        this.state.hasPolygon = true;
    }

    cancelDrawing() {
        this._removeClickListener();
        if (this.tempPolyline) {
            this.tempPolyline.setMap(null);
            this.tempPolyline = null;
        }
        this.tempPoints = [];
        this.state.drawing = false;
        this.state.canFinish = false;
    }

    _removeClickListener() {
        if (this.mapClickListener) {
            google.maps.event.removeListener(this.mapClickListener);
            this.mapClickListener = null;
        }
    }

    _bindPolygonEvents(poly) {
        const path = poly.getPath();
        ["insert_at", "remove_at", "set_at"].forEach((eventName) => {
            google.maps.event.addListener(path, eventName, () => this._commit(poly));
        });
    }

    _commit(poly) {
        const coords = poly
            .getPath()
            .getArray()
            .map((p) => [p.lng(), p.lat()]);
        if (coords.length) {
            coords.push(coords[0]);
        }
        const geojson = { type: "Polygon", coordinates: [coords] };
        this.props.record.update({ [this.props.name]: JSON.stringify(geojson) });
        this._updateAreaPreview(poly);
    }

    _updateAreaPreview(poly) {
        const areaM2 = google.maps.geometry.spherical.computeArea(poly.getPath());
        this.state.areaHa = (areaM2 / 10000).toFixed(4);
    }

    _centroid(ring) {
        const lats = ring.map((c) => c[1]);
        const lngs = ring.map((c) => c[0]);
        return {
            lat: (Math.min(...lats) + Math.max(...lats)) / 2,
            lng: (Math.min(...lngs) + Math.max(...lngs)) / 2,
        };
    }
}

export const paoPolygonMapField = { component: PaoPolygonMapField };
registry.category("fields").add("pao_polygon_map", paoPolygonMapField);
