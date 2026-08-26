/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadGoogleMapsApi } from "./pao_google_maps_loader";
import { Component, onMounted, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";

const DROPDOWN_MAX_HEIGHT = 220;

// One distinct color per site (cycled by position), so neighboring polygons
// are easy to tell apart regardless of their review state.
const SITE_COLOR_PALETTE = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
    "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990",
    "#dcbeff", "#9a6324", "#800000", "#aaffc3", "#000075",
];

const SERVICE_FIELDS = [
    "id", "product_id", "site_ids", "calidad_qty",
    "external_partner_id", "external_qty", "final_qty",
    "estimate_source", "sale_order_line_id",
];

const PRODUCT_SEARCH_DEBOUNCE_MS = 250;

// Google's Directions API caps a single request at 25 locations
// (origin + destination + up to 23 intermediate waypoints).
const MAX_DIRECTIONS_WAYPOINTS = 25;

export class PaoSitePlotOverviewMap extends Component {
    static template = "pao_site_plot_survey.SitePlotOverviewMap";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.mapContainerRef = useRef("mapContainer");
        this.productSearchInputRef = useRef("productSearchInput");
        this.siteTagBoxRef = useRef("siteTagBox");
        this.state = useState({
            error: null,
            sites: [],
            services: [],
            newService: { product_id: false, site_ids: [], calidad_qty: 0 },
            productSearch: { text: "", results: [], open: false, style: "" },
            siteTagPicker: { open: false, text: "", style: "" },
            measuring: false,
            distanceText: "",
            siteChainDistanceText: "",
            drivingRoute: { loading: false, distanceText: "", durationText: "", error: "" },
        });
        this.measurePoints = [];
        this.measurePolyline = null;
        this.measureMarkers = [];
        this.measureClickListener = null;
        this.productSearchTimeout = null;
        this.dropdownScrollCloseHandler = null;
        this.siteChainPolyline = null;
        this.chainOrderedPoints = [];
        this.directionsService = null;
        this.directionsRenderer = null;

        this.saleOrderId =
            this.props.action.context.active_id || this.props.action.context.default_sale_order_id;

        onWillStart(async () => {
            if (!this.saleOrderId) {
                this.state.error = "No se encontró la cotización.";
                return;
            }
            const apiKey = await this.orm.call("ir.config_parameter", "get_pao_google_maps_api_key", []);
            if (!apiKey) {
                this.state.error = "Configure la API key de Google Maps en Ajustes.";
                return;
            }
            this.state.sites = await this.orm.searchRead(
                "pao.site.plot",
                [["sale_order_id", "=", this.saleOrderId]],
                ["name", "geojson_polygon", "computed_surface_ha", "declared_surface_ha",
                 "state", "location", "variety"]
            );
            await this._loadServices();
            try {
                await loadGoogleMapsApi(apiKey);
            } catch {
                this.state.error = "No se pudo cargar Google Maps.";
            }
        });
        onMounted(() => {
            if (!this.state.error) {
                this._initMap();
            }
        });
        onWillUnmount(() => {
            this._clearDropdownScrollClose();
            if (this.directionsRenderer) {
                this.directionsRenderer.setMap(null);
            }
        });
    }

    /** Anchors a dropdown to `el` using position:fixed (viewport-relative),
     * so it can never be clipped by a scrolling ancestor (the table wrapper,
     * the panel, the page...) the way position:absolute was. Flips upward
     * when there isn't enough room below. */
    _computeDropdownStyle(el) {
        const rect = el.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        const openUpward = spaceBelow < DROPDOWN_MAX_HEIGHT && rect.top > spaceBelow;
        const top = openUpward ? rect.top - Math.min(DROPDOWN_MAX_HEIGHT, rect.top) : rect.bottom;
        return `position:fixed; left:${rect.left}px; width:${rect.width}px; top:${top}px; `
             + `max-height:${DROPDOWN_MAX_HEIGHT}px; overflow-y:auto; z-index:1060;`;
    }

    /** Closes `closeFn` the moment the page (or any scrollable ancestor) is
     * scrolled, since a position:fixed dropdown doesn't follow its anchor. */
    _watchScrollToClose(closeFn) {
        this._clearDropdownScrollClose();
        this.dropdownScrollCloseHandler = () => {
            closeFn();
            this._clearDropdownScrollClose();
        };
        window.addEventListener("scroll", this.dropdownScrollCloseHandler, true);
    }

    _clearDropdownScrollClose() {
        if (this.dropdownScrollCloseHandler) {
            window.removeEventListener("scroll", this.dropdownScrollCloseHandler, true);
            this.dropdownScrollCloseHandler = null;
        }
    }

    _siteName(siteId) {
        const site = this.state.sites.find((s) => s.id === siteId);
        return site ? site.name : siteId;
    }

    _siteColor(siteId) {
        const idx = this.state.sites.findIndex((s) => s.id === siteId);
        return SITE_COLOR_PALETTE[Math.max(idx, 0) % SITE_COLOR_PALETTE.length];
    }

    _initMap() {
        this.map = new google.maps.Map(this.mapContainerRef.el, {
            mapTypeId: "satellite",
            zoom: 14,
            center: { lat: 23.6, lng: -102.5 },
        });

        const bounds = new google.maps.LatLngBounds();
        const chainEntries = [];

        this.state.sites.forEach((site, index) => {
            if (!site.geojson_polygon) {
                return;
            }
            let geo;
            try {
                geo = JSON.parse(site.geojson_polygon);
            } catch {
                return;
            }
            const path = geo.coordinates[0].map(([lng, lat]) => ({ lat, lng }));
            path.forEach((p) => bounds.extend(p));
            const color = SITE_COLOR_PALETTE[index % SITE_COLOR_PALETTE.length];

            const polygon = new google.maps.Polygon({
                paths: path,
                map: this.map,
                strokeColor: color,
                fillColor: color,
                fillOpacity: 0.25,
                strokeWeight: 2,
                clickable: true,
            });
            // Polygon clicks don't bubble to the map's own "click" listener,
            // so forward them manually while a measurement is in progress -
            // otherwise clicking on top of a site would never register as a
            // measurement point.
            polygon.addListener("click", (ev) => {
                if (this.state.measuring) {
                    this._addMeasurePoint(ev.latLng);
                }
            });

            const centroid = this._centroid(path);
            chainEntries.push({ site, point: centroid });
        });

        const orderedEntries = this._optimizeChainOrder(chainEntries);
        // Numbered per the final chain order (not the sites list order), so
        // the number on the map matches the stop sequence used both by the
        // black line and by "Calcular ruta en carro" - a quick visual way to
        // confirm both follow the exact same order.
        orderedEntries.forEach((entry, i) => {
            new google.maps.Marker({
                position: entry.point,
                map: this.map,
                clickable: false,
                label: { text: `${i + 1}. ${entry.site.name}`, color: "#ffffff", fontWeight: "bold", fontSize: "12px" },
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 0,
                    labelOrigin: new google.maps.Point(0, 0),
                },
            });
        });

        this.chainOrderedPoints = orderedEntries.map((entry) => entry.point);
        this._drawSiteChain(this.chainOrderedPoints);

        if (!bounds.isEmpty()) {
            this.map.fitBounds(bounds);
        } else {
            this.map.setZoom(5);
        }
    }

    /** Reorders the sites (kept as {site, point} entries, so the site each
     * stop belongs to travels along with its coordinates) into a short (not
     * necessarily perfectly optimal - exact TSP is impractical to compute
     * live) open path: nearest-neighbor construction tried from every
     * possible starting point, kept as the shortest, then refined with
     * 2-opt swaps. The order the user happened to create/import the sites
     * in is not a good proxy for which ones are actually close to each
     * other. */
    _optimizeChainOrder(entries) {
        if (entries.length < 3) {
            return entries;
        }
        let best = null;
        let bestLen = Infinity;
        for (let start = 0; start < entries.length; start++) {
            const path = this._nearestNeighborPathFrom(entries, start);
            const len = this._pathLength(path);
            if (len < bestLen) {
                bestLen = len;
                best = path;
            }
        }
        return this._twoOptImprove(best);
    }

    _nearestNeighborPathFrom(entries, startIndex) {
        const remaining = entries.map((_, i) => i).filter((i) => i !== startIndex);
        const order = [startIndex];
        while (remaining.length) {
            const last = entries[order[order.length - 1]].point;
            let bestPos = 0;
            let bestDist = Infinity;
            remaining.forEach((idx, pos) => {
                const d = google.maps.geometry.spherical.computeDistanceBetween(last, entries[idx].point);
                if (d < bestDist) {
                    bestDist = d;
                    bestPos = pos;
                }
            });
            order.push(remaining.splice(bestPos, 1)[0]);
        }
        return order.map((i) => entries[i]);
    }

    _pathLength(entries) {
        let total = 0;
        for (let i = 1; i < entries.length; i++) {
            total += google.maps.geometry.spherical.computeDistanceBetween(entries[i - 1].point, entries[i].point);
        }
        return total;
    }

    /** Standard 2-opt local search for an open path: repeatedly reverses a
     * segment whenever doing so shortens the two edges at its boundaries,
     * until no more improving swap is found (capped for safety). */
    _twoOptImprove(entries) {
        let best = entries.slice();
        const distance = (a, b) => google.maps.geometry.spherical.computeDistanceBetween(a.point, b.point);
        let improved = true;
        let iterations = 0;
        const maxIterations = 200;
        while (improved && iterations < maxIterations) {
            improved = false;
            iterations++;
            for (let i = 0; i < best.length - 2; i++) {
                for (let j = i + 2; j < best.length; j++) {
                    const hasTailEdge = j + 1 < best.length;
                    const currentLength =
                        distance(best[i], best[i + 1]) + (hasTailEdge ? distance(best[j], best[j + 1]) : 0);
                    const swappedLength =
                        distance(best[i], best[j]) + (hasTailEdge ? distance(best[i + 1], best[j + 1]) : 0);
                    if (swappedLength < currentLength - 1e-6) {
                        const reversed = best.slice(i + 1, j + 1).reverse();
                        best = best.slice(0, i + 1).concat(reversed, best.slice(j + 1));
                        improved = true;
                    }
                }
            }
        }
        return best;
    }

    /** Connects every drawn site's centroid, in the order given, with a
     * single open polyline (no closing segment back to the start - "en forma
     * de culebra") and shows the sum of each leg's distance, so Calidad gets
     * an at-a-glance read of how spread out the sites are without having to
     * measure manually. */
    _drawSiteChain(points) {
        if (this.siteChainPolyline) {
            this.siteChainPolyline.setMap(null);
            this.siteChainPolyline = null;
        }
        if (points.length < 2) {
            this.state.siteChainDistanceText = "";
            return;
        }
        this.siteChainPolyline = new google.maps.Polyline({
            path: points,
            map: this.map,
            clickable: false,
            strokeColor: "#000000",
            strokeOpacity: 0.9,
            strokeWeight: 3,
        });
        let totalM = 0;
        for (let i = 1; i < points.length; i++) {
            totalM += google.maps.geometry.spherical.computeDistanceBetween(points[i - 1], points[i]);
        }
        this.state.siteChainDistanceText = this._formatDistance(totalM);
    }

    /** Asks Google's Directions API for an actual driving route following
     * the same site order as the black "culebra" line (not re-optimized by
     * Google, so both lines describe the same sequence of stops - one as
     * the crow flies, one as a car would actually drive it), then shows the
     * total real driving distance and time. Requires the Directions API to
     * be enabled for the configured Google Maps API key. */
    async calculateDrivingRoute() {
        const points = this.chainOrderedPoints;
        if (points.length < 2) {
            this.notification.add("Se necesitan al menos 2 sitios con polígono para calcular una ruta.", { type: "warning" });
            return;
        }

        let routePoints = points;
        if (routePoints.length > MAX_DIRECTIONS_WAYPOINTS) {
            routePoints = routePoints.slice(0, MAX_DIRECTIONS_WAYPOINTS);
            this.notification.add(
                `Google limita las rutas a ${MAX_DIRECTIONS_WAYPOINTS} paradas; se calculará solo con las primeras ${MAX_DIRECTIONS_WAYPOINTS} de la lista.`,
                { type: "warning" }
            );
        }

        this.state.drivingRoute = { loading: true, distanceText: "", durationText: "", error: "" };

        if (!this.directionsService) {
            this.directionsService = new google.maps.DirectionsService();
        }
        if (!this.directionsRenderer) {
            this.directionsRenderer = new google.maps.DirectionsRenderer({
                map: this.map,
                suppressMarkers: true,
                preserveViewport: true,
                polylineOptions: { strokeColor: "#1a73e8", strokeWeight: 4, strokeOpacity: 0.8 },
            });
        }

        const waypoints = routePoints.slice(1, -1).map((location) => ({ location, stopover: true }));
        try {
            const result = await this.directionsService.route({
                origin: routePoints[0],
                destination: routePoints[routePoints.length - 1],
                waypoints,
                optimizeWaypoints: false,
                travelMode: google.maps.TravelMode.DRIVING,
            });
            this.directionsRenderer.setDirections(result);

            let totalMeters = 0;
            let totalSeconds = 0;
            for (const leg of result.routes[0].legs) {
                totalMeters += leg.distance.value;
                totalSeconds += leg.duration.value;
            }
            this.state.drivingRoute = {
                loading: false,
                distanceText: this._formatDistance(totalMeters),
                durationText: this._formatDuration(totalSeconds),
                error: "",
            };
        } catch {
            this.state.drivingRoute = {
                loading: false,
                distanceText: "",
                durationText: "",
                error: "No se pudo calcular la ruta en carro (puede que algún sitio no tenga acceso por carretera, "
                     + "o que la Directions API no esté habilitada para esta clave de Google Maps).",
            };
        }
    }

    _formatDuration(totalSeconds) {
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.round((totalSeconds % 3600) / 60);
        if (hours > 0) {
            return `${hours} h ${minutes} min`;
        }
        return `${minutes} min`;
    }

    toggleMeasure() {
        if (this.state.measuring) {
            this._stopMeasuring();
        } else {
            this._startMeasuring();
        }
    }

    _startMeasuring() {
        this.measurePoints = [];
        this.measurePolyline = new google.maps.Polyline({
            map: this.map,
            strokeColor: "#ff0000",
            strokeWeight: 2,
        });
        this.state.measuring = true;
        this.state.distanceText = "0 m";
        this.measureClickListener = google.maps.event.addListener(this.map, "click", (ev) =>
            this._addMeasurePoint(ev.latLng)
        );
    }

    _addMeasurePoint(latLng) {
        this.measurePoints.push(latLng);
        this.measurePolyline.setPath(this.measurePoints);
        this.measureMarkers.push(
            new google.maps.Marker({
                position: latLng,
                map: this.map,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 4,
                    fillColor: "#ff0000",
                    fillOpacity: 1,
                    strokeWeight: 0,
                },
            })
        );
        this._updateDistance();
    }

    _updateDistance() {
        let totalM = 0;
        for (let i = 1; i < this.measurePoints.length; i++) {
            totalM += google.maps.geometry.spherical.computeDistanceBetween(
                this.measurePoints[i - 1],
                this.measurePoints[i]
            );
        }
        this.state.distanceText = this._formatDistance(totalM);
    }

    _formatDistance(totalM) {
        return totalM >= 1000 ? (totalM / 1000).toFixed(2) + " km" : totalM.toFixed(0) + " m";
    }

    _stopMeasuring() {
        if (this.measureClickListener) {
            google.maps.event.removeListener(this.measureClickListener);
            this.measureClickListener = null;
        }
        this.state.measuring = false;
    }

    clearMeasure() {
        this._stopMeasuring();
        if (this.measurePolyline) {
            this.measurePolyline.setMap(null);
            this.measurePolyline = null;
        }
        this.measureMarkers.forEach((m) => m.setMap(null));
        this.measureMarkers = [];
        this.measurePoints = [];
        this.state.distanceText = "";
    }

    _centroid(path) {
        const lats = path.map((p) => p.lat);
        const lngs = path.map((p) => p.lng);
        return {
            lat: (Math.min(...lats) + Math.max(...lats)) / 2,
            lng: (Math.min(...lngs) + Math.max(...lngs)) / 2,
        };
    }

    // ── Servicios estimados ──────────────────────────────────────────────
    async _loadServices() {
        this.state.services = await this.orm.searchRead(
            "pao.site.plot.service",
            [["sale_order_id", "=", this.saleOrderId]],
            SERVICE_FIELDS
        );
    }

    /** Sites already assigned to some existing service line - these can't be
     * picked again on a new line, so a site only ever belongs to one service. */
    _usedSiteIds() {
        const used = new Set();
        for (const service of this.state.services) {
            for (const siteId of service.site_ids) {
                used.add(siteId);
            }
        }
        return used;
    }

    availableSitesForPicker() {
        const used = this._usedSiteIds();
        const alreadyPicked = new Set(this.state.newService.site_ids);
        const text = this.state.siteTagPicker.text.trim().toLowerCase();
        return this.state.sites.filter((site) => {
            if (used.has(site.id) || alreadyPicked.has(site.id)) {
                return false;
            }
            return !text || site.name.toLowerCase().includes(text);
        });
    }

    // ── Product search (by name or reference, like the sale order lines) ──
    onProductSearchInput(ev) {
        this.state.productSearch.text = ev.target.value;
        this.state.newService.product_id = false;
        this.state.newService.productLabel = "";
        clearTimeout(this.productSearchTimeout);
        const text = ev.target.value.trim();
        if (!text) {
            this.state.productSearch.results = [];
            this.state.productSearch.open = false;
            return;
        }
        this.productSearchTimeout = setTimeout(() => this._searchProducts(text), PRODUCT_SEARCH_DEBOUNCE_MS);
    }

    async _searchProducts(text) {
        const results = await this.orm.searchRead(
            "product.product",
            ["&", ["type", "=", "service"], "|", ["name", "ilike", text], ["default_code", "ilike", text]],
            ["id", "name", "default_code"],
            { limit: 8 }
        );
        this.state.productSearch.results = results;
        if (results.length && this.productSearchInputRef.el) {
            this.state.productSearch.style = this._computeDropdownStyle(this.productSearchInputRef.el);
            this.state.productSearch.open = true;
            this._watchScrollToClose(() => (this.state.productSearch.open = false));
        }
    }

    selectProduct(product) {
        this.state.newService.product_id = product.id;
        const label = product.default_code ? `[${product.default_code}] ${product.name}` : product.name;
        this.state.newService.productLabel = label;
        this.state.productSearch.text = label;
        this.state.productSearch.open = false;
        this.state.productSearch.results = [];
        this._clearDropdownScrollClose();
    }

    onProductFocus() {
        if (this.state.productSearch.results.length && this.productSearchInputRef.el) {
            this.state.productSearch.style = this._computeDropdownStyle(this.productSearchInputRef.el);
            this.state.productSearch.open = true;
            this._watchScrollToClose(() => (this.state.productSearch.open = false));
        }
    }

    closeProductDropdown() {
        // Small delay so a click on a dropdown result registers before it closes.
        setTimeout(() => {
            this.state.productSearch.open = false;
            this._clearDropdownScrollClose();
        }, 150);
    }

    // ── Site tag picker (new service row) ──────────────────────────────────
    toggleSiteTagPicker() {
        const opening = !this.state.siteTagPicker.open;
        this.state.siteTagPicker.open = opening;
        this.state.siteTagPicker.text = "";
        if (opening && this.siteTagBoxRef.el) {
            this.state.siteTagPicker.style = this._computeDropdownStyle(this.siteTagBoxRef.el);
            this._watchScrollToClose(() => (this.state.siteTagPicker.open = false));
        } else {
            this._clearDropdownScrollClose();
        }
    }

    onSiteTagSearchInput(ev) {
        this.state.siteTagPicker.text = ev.target.value;
    }

    addSiteTag(siteId) {
        this.state.newService.site_ids.push(siteId);
        this.state.siteTagPicker.text = "";
    }

    removeSiteTag(siteId) {
        const idx = this.state.newService.site_ids.indexOf(siteId);
        if (idx !== -1) {
            this.state.newService.site_ids.splice(idx, 1);
        }
    }

    async addService() {
        if (!this.state.newService.product_id) {
            this.notification.add("Selecciona un servicio.", { type: "warning" });
            return;
        }
        if (!this.state.newService.site_ids.length) {
            this.notification.add("Selecciona al menos un sitio.", { type: "warning" });
            return;
        }
        await this.orm.create("pao.site.plot.service", [{
            sale_order_id: this.saleOrderId,
            product_id: this.state.newService.product_id,
            site_ids: [[6, 0, this.state.newService.site_ids]],
            calidad_qty: this.state.newService.calidad_qty,
        }]);
        this.state.newService = { product_id: false, site_ids: [], calidad_qty: 0 };
        this.state.productSearch = { text: "", results: [], open: false };
        this.state.siteTagPicker = { open: false, text: "" };
        await this._loadServices();
    }

    async onServiceQtyChange(service, ev) {
        const value = parseFloat(ev.target.value) || 0;
        service.calidad_qty = value;
        await this.orm.write("pao.site.plot.service", [service.id], { calidad_qty: value });
    }

    async removeService(service) {
        await this.orm.unlink("pao.site.plot.service", [service.id]);
        await this._loadServices();
    }
}

registry.category("actions").add("pao_site_plot_overview_map", PaoSitePlotOverviewMap);
