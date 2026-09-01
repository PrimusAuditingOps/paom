/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted } from "@odoo/owl";

const META_ANUAL = 80;

class EnaDashboard extends Component {
    static template = "pao_globalgap_ena.EnaDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            anio: new Date().getFullYear(),
            // Contadores generales
            total: 0,
            realizadas: 0,
            programadas: 0,
            no_realizadas: 0,
            candidatos: 0,
            en_proceso: 0,
            // Alertas
            vencidas: 0,
            proximas: 0,
            // Por coordinadora
            por_coordinadora: [],
            // Por mes
            por_mes: Array(12).fill(0),
        });
        onMounted(() => this._cargarDatos());
    }

    async _cargarDatos() {
        this.state.loading = true;
        const anio = this.state.anio;

        // ── Totales por etapa ──────────────────────────────────────────────
        const grupos = await this.orm.readGroup(
            "ena.solicitud",
            [["anio", "=", anio]],
            ["stage"],
            ["stage"]
        );
        let total = 0;
        const conteo = {};
        for (const g of grupos) {
            conteo[g.stage] = g.stage_count;
            total += g.stage_count;
        }
        this.state.total       = total;
        this.state.realizadas  = conteo["realizada"]   || 0;
        this.state.programadas = conteo["programada"]  || 0;
        this.state.no_realizadas = conteo["no_realizada"] || 0;
        this.state.candidatos  = conteo["candidato"]   || 0;
        this.state.en_proceso  = (conteo["asignada"] || 0)
                               + (conteo["notificada"]    || 0);

        // ── Alertas de ventana ────────────────────────────────────────────
        const alertas = await this.orm.readGroup(
            "ena.solicitud",
            [["anio", "=", anio], ["stage", "not in", ["realizada", "no_realizada"]]],
            ["alerta_ventana"],
            ["alerta_ventana"]
        );
        for (const a of alertas) {
            if (a.alerta_ventana === "vencido")  this.state.vencidas  = a.alerta_ventana_count;
            if (a.alerta_ventana === "proximo")  this.state.proximas  = a.alerta_ventana_count;
        }

        // ── Por coordinadora ──────────────────────────────────────────────
        const porCoord = await this.orm.readGroup(
            "ena.solicitud",
            [["anio", "=", anio], ["coordinadora_id", "!=", false]],
            ["coordinadora_id", "stage"],
            ["coordinadora_id", "stage"],
            { lazy: false }
        );
        const coordMap = {};
        for (const r of porCoord) {
            const id   = r.coordinadora_id[0];
            const name = r.coordinadora_id[1];
            if (!coordMap[id]) {
                coordMap[id] = { id, name, realizadas: 0, en_proceso: 0, total: 0 };
            }
            coordMap[id].total += r.__count;
            if (r.stage === "realizada") coordMap[id].realizadas += r.__count;
            else coordMap[id].en_proceso += r.__count;
        }
        this.state.por_coordinadora = Object.values(coordMap)
            .sort((a, b) => b.total - a.total);

        // ── Por mes (ENAs realizadas) ─────────────────────────────────────
        const porMes = await this.orm.readGroup(
            "ena.solicitud",
            [
                ["anio", "=", anio],
                ["stage", "=", "realizada"],
                ["month", "!=", false]
            ],
            ["month"],
            ["month"]
        );
        const meses = Array(12).fill(0);
        for (const r of porMes) {
            
            meses[r.month - 1] += r.month_count;
        }
        this.state.por_mes = meses;
        this.state.loading = false;
    }

    get porcentajeMeta() {
        return Math.min(100, Math.round((this.state.realizadas / META_ANUAL) * 100));
    }

    get colorMeta() {
        const p = this.porcentajeMeta;
        if (p >= 80) return "#1e8449";
        if (p >= 50) return "#d4ac0d";
        return "#cb4335";
    }

    get maxBarMes() {
        return Math.max(...this.state.por_mes, 1);
    }

    // ── Navegación rápida ─────────────────────────────────────────────────
    _irALista(domain_extra) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Auditorías No Anunciadas",
            res_model: "ena.solicitud",
            view_mode: "list,form",
            domain: [["anio", "=", this.state.anio], ...domain_extra],
        });
    }

    onClickRealizadas()   { this._irALista([["stage", "=", "realizada"]]); }
    onClickProgramadas()  { this._irALista([["stage", "=", "programada"]]); }
    onClickVencidas()     { this._irALista([["alerta_ventana", "=", "vencido"]]); }
    onClickProximas()     { this._irALista([["alerta_ventana", "=", "proximo"]]); }
    onClickCandidatos()   { this._irALista([["stage", "=", "candidato"]]); }
    onClickEnProceso()    { this._irALista([["stage", "in", ["asignada", "notificada"]]]); }
    onClickNoRealizadas() { this._irALista([["stage", "=", "no_realizada"]]); }

    onClickCoordinadora(coord) {
        this._irALista([["coordinadora_id", "=", coord.id]]);
    }
}

registry.category("actions").add("ena_dashboard", EnaDashboard);
