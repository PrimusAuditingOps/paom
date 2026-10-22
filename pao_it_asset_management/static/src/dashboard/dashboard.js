/** @odoo-module **/
// Tablero de inicio de IT Asset Management. Solo pinta: los datos y las
// etiquetas (ya traducidas) vienen de pao.it.dashboard (Python).
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const CHART_COLORS = [
    "#4c6ef5", "#7950f2", "#15aabf", "#40c057", "#fab005",
    "#fd7e14", "#e64980", "#868e96", "#228be6", "#12b886",
];
const EVENT_COLORS = {
    maintenance: "#7950f2",
    warranty: "#e03131",
    subscription: "#f59f00",
    transit: "#1c7ed6",
};

export class ItAssetDashboard extends Component {
    static template = "pao_it_asset_management.ItAssetDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        const today = new Date();
        this.state = useState({
            data: null,
            calendar: null,
            companyIds: [],
            dateFrom: `${today.getFullYear()}-01-01`,
            dateTo: `${today.getFullYear()}-12-31`,
            kind: "hardware",
            calYear: today.getFullYear(),
            calMonth: today.getMonth() + 1,
        });
        this.eventColors = EVENT_COLORS;
        this.eventTypes = Object.keys(EVENT_COLORS);
        onWillStart(() => this.loadAll());
    }

    async loadAll() {
        await Promise.all([this.loadData(), this.loadCalendar()]);
    }

    async loadData() {
        const data = await this.orm.call("pao.it.dashboard", "get_dashboard_data", [], {
            company_ids: this.state.companyIds,
            date_from: this.state.dateFrom,
            date_to: this.state.dateTo,
            kind: this.state.kind,
        });
        this.state.companyIds = data.company_ids;
        this.state.data = data;
    }

    async loadCalendar() {
        this.state.calendar = await this.orm.call("pao.it.dashboard", "get_calendar_events", [], {
            company_ids: this.state.companyIds,
            year: this.state.calYear,
            month: this.state.calMonth,
        });
    }

    // ---------------- Filtros ----------------
    async toggleCompany(companyId) {
        const ids = new Set(this.state.companyIds);
        if (ids.has(companyId)) {
            if (ids.size === 1) {
                return; // al menos una compañía
            }
            ids.delete(companyId);
        } else {
            ids.add(companyId);
        }
        this.state.companyIds = [...ids];
        await this.loadAll();
    }

    async onDateChange(field, ev) {
        this.state[field] = ev.target.value;
        await this.loadData();
    }

    async setKind(kind) {
        this.state.kind = kind;
        await this.loadData();
    }

    async moveMonth(delta) {
        let month = this.state.calMonth + delta;
        let year = this.state.calYear;
        if (month < 1) {
            month = 12;
            year -= 1;
        } else if (month > 12) {
            month = 1;
            year += 1;
        }
        this.state.calMonth = month;
        this.state.calYear = year;
        await this.loadCalendar();
    }

    // ---------------- Navegación ----------------
    openCount(count) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: count.model,
            domain: count.domain,
            views: [[false, "list"], [false, "form"]],
            target: "current",
            context: { pao_it_show_company: true },
        });
    }

    openEvent(event) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: event.model,
            res_id: event.res_id,
            views: [[false, "form"]],
            target: "current",
            context: { pao_it_show_company: true },
        });
    }

    // ---------------- Formato ----------------
    money(value) {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0,
        }).format(value || 0);
    }

    percent(part, total) {
        return total ? `${Math.round((part / total) * 100)}%` : "0%";
    }

    // ---------------- Gráfica (SVG propio) ----------------
    get chartSlices() {
        const items = (this.state.data && this.state.data.chart) || [];
        const total = items.reduce((sum, item) => sum + item.value, 0);
        if (!total) {
            return [];
        }
        const cx = 100, cy = 100, r = 90;
        let angle = -Math.PI / 2;
        return items.map((item, index) => {
            const fraction = item.value / total;
            const start = angle;
            const end = angle + fraction * 2 * Math.PI;
            angle = end;
            const large = end - start > Math.PI ? 1 : 0;
            const x1 = cx + r * Math.cos(start), y1 = cy + r * Math.sin(start);
            const x2 = cx + r * Math.cos(end), y2 = cy + r * Math.sin(end);
            // Una sola rebanada (100%): círculo completo.
            const path = fraction >= 0.9999
                ? `M ${cx - r} ${cy} A ${r} ${r} 0 1 1 ${cx + r} ${cy} A ${r} ${r} 0 1 1 ${cx - r} ${cy} Z`
                : `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`;
            return {
                path,
                color: CHART_COLORS[index % CHART_COLORS.length],
                label: item.label,
                value: item.value,
                pct: Math.round(fraction * 100),
            };
        });
    }

    // ---------------- Calendario ----------------
    get calendarWeeks() {
        const cal = this.state.calendar;
        if (!cal) {
            return [];
        }
        const cells = [];
        for (let i = 0; i < cal.first_weekday; i++) {
            cells.push({ day: null, events: [], key: `e${i}` });
        }
        for (let day = 1; day <= cal.days; day++) {
            const iso = `${cal.year}-${String(cal.month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
            cells.push({
                day,
                key: `d${day}`,
                isToday: iso === cal.today,
                events: cal.events.filter((event) => event.day === day),
            });
        }
        while (cells.length % 7) {
            cells.push({ day: null, events: [], key: `t${cells.length}` });
        }
        const weeks = [];
        for (let i = 0; i < cells.length; i += 7) {
            weeks.push({ key: `w${i}`, cells: cells.slice(i, i + 7) });
        }
        return weeks;
    }
}

registry.category("actions").add("pao_it_asset_dashboard", ItAssetDashboard);
