/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

// ── Colores del sistema de diseño ─────────────────────────────────────────────
const COLORS = {
    blue: { bg: 'rgba(55, 138, 221, 0.85)', border: '#185FA5' },
    green: { bg: 'rgba(99, 153, 34, 0.85)', border: '#3B6D11' },
    teal: { bg: 'rgba(29, 158, 117, 0.85)', border: '#0F6E56' },
    red: { bg: 'rgba(226, 75, 74, 0.85)', border: '#A32D2D' },
    amber: { bg: 'rgba(186, 117, 23, 0.85)', border: '#854F0B' },
    gray: { bg: 'rgba(136, 135, 128, 0.85)', border: '#5F5E5A' },
    purple: { bg: 'rgba(127, 119, 221, 0.85)', border: '#534AB7' },
};

// ── Utilidades ────────────────────────────────────────────────────────────────
function pct(num, total) {
    if (!total) return '0%';
    return `${Math.round((num / total) * 100)}%`;
}

function barPct(value, list) {
    const max = Math.max(...list.map(i => i[1]), 1);
    return Math.round((value / max) * 100);
}

function buildDoughnut(ctx, labels, values, colors) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors.map(c => COLORS[c].bg),
                borderColor: colors.map(c => COLORS[c].border),
                borderWidth: 1.5,
            }],
        },
        options: {
            responsive: true,
            cutout: '65%',
            plugins: {
                legend: { onClick: null, position: 'bottom', labels: { boxWidth: 12, font: { size: 12 } } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const val = ctx.parsed;
                            const p = total ? Math.round((val / total) * 100) : 0;
                            return ` ${ctx.label}: ${val} (${p}%)`;
                        },
                    },
                },
            },
        },
    });
}

function buildBar(ctx, labels, values, color) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: COLORS[color].bg,
                borderColor: COLORS[color].border,
                borderWidth: 1.5,
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,

            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const val = ctx.parsed.y;
                            const p = total ? Math.round((val / total) * 100) : 0;
                            return ` ${val} (${p}%)`;
                        },
                    },
                },
            },

            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                },
            },
        },
    });
}

// ── Componente OWL ────────────────────────────────────────────────────────────
class SurveyAuditDashboard extends Component {
    static template = "pao_survey_audit_automation.SurveyAuditDashboard";

    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");

        // Estado inicial: rango = últimos 90 días
        const today = new Date();
        const past = new Date(today);
        past.setDate(past.getDate() - 90);

        this.state = useState({
            loading: false,
            dateFrom: past.toISOString().slice(0, 10),
            dateTo: today.toISOString().slice(0, 10),
            surveyId: null,
            surveys: [],
            data: null,
        });

        // Instancias de Chart.js para poder destruirlas al remontar
        this._charts = [];

        onMounted(() => this._loadSurveysList());
        onWillUnmount(() => this._destroyCharts());
    }

    // ── Helpers de template ──────────────────────────────────────────────────
    pct(num, total) { return pct(num, total); }
    barPct(value, list) { return barPct(value, list); }

    // ── Eventos ──────────────────────────────────────────────────────────────
    onDateChange(field, ev) {
        this.state[field] = ev.target.value;
    }

    onSurveyChange(ev) {
        this.state.surveyId = ev.target.value ? parseInt(ev.target.value) : null;
    }

    async printDashboard() {
        // Load libraries dynamically if not already loaded
        if (!window.html2canvas) {
            await this._loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js');
        }
        if (!window.jspdf) {
            await this._loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js');
        }

        const el = document.querySelector('.o_survey_audit_dashboard');
        if (!el) return;

        const surveyTitle = this.state.surveys.find(
            s => s.id === this.state.surveyId
        )?.title || 'dashboard';

        try {
            const canvas = await html2canvas(el, {
                scale: 2,
                useCORS: true,
                allowTaint: true,
                backgroundColor: '#f9f9f9',
                scrollX: 0,
                scrollY: -window.scrollY,
                windowWidth: el.scrollWidth,
                windowHeight: el.scrollHeight,
            });

            const imgData = canvas.toDataURL('image/png');
            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF({
                orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
                unit: 'px',
                format: [canvas.width / 2, canvas.height / 2],
            });

            pdf.addImage(imgData, 'PNG', 0, 0, canvas.width / 2, canvas.height / 2);
            pdf.save(`${surveyTitle}.pdf`);
        } catch (err) {
            this.notification.add(
                'Error generating PDF: ' + (err.message || err),
                { type: 'danger' }
            );
        }
    }

    _loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // ── Carga de datos ───────────────────────────────────────────────────────
    async loadData() {

        if (!this.state.surveyId) {
            await this._loadSurveysList();
            return;
        }

        this.state.data = null;
        this.state.loading = true;
        this._destroyCharts();

        try {
            const data = await this.rpc("/web/dataset/call_kw", {
                model: "survey.survey",
                method: "get_dashboard_data",
                args: [],
                kwargs: {
                    date_from: this.state.dateFrom,
                    date_to: this.state.dateTo,
                    survey_id: this.state.surveyId,
                },
            });

            data.top_compliment_tags = data.top_compliment_tags || [];
            data.top_complaint_tags = data.top_complaint_tags || [];
            data.top_auditors_compliments = data.top_auditors_compliments || [];
            data.top_auditors_complaints = data.top_auditors_complaints || [];
            data.top_coordinators_compliments = data.top_coordinators_compliments || [];
            data.top_coordinators_complaints = data.top_coordinators_complaints || [];

            if (!this.state.surveys || this.state.surveys.length === 0) {
                this.state.surveys = data.surveys || [];
            }

            this.state.data = data;

            // Charts se renderizan en el siguiente tick (DOM actualizado)
            setTimeout(() => this._renderCharts(data), 50);
        } catch (err) {
            this.notification.add(
                _t("Error loading dashboard data: ") + (err.message || err),
                { type: "danger" }
            );
        } finally {
            this.state.loading = false;
        }
    }

    async _loadSurveysList() {
        try {
            const data = await this.rpc("/web/dataset/call_kw", {
                model: "survey.survey",
                method: "get_dashboard_data",
                args: [],
                kwargs: {
                    date_from: this.state.dateFrom,
                    date_to: this.state.dateTo,
                    survey_id: null,
                },
            });
            if (!this.state.surveys || this.state.surveys.length === 0) {
                this.state.surveys = data.surveys || [];
            }
        } catch (err) {
            this.notification.add(
                "Error loading surveys list: " + (err.message || err),
                { type: "danger" }
            );
        }
    }

    // ── Renderizado de gráficas ──────────────────────────────────────────────
    _renderCharts(d) {
        this._destroyCharts();

        const answered = d.total_answered;
        const unanswered = Math.max(d.total_sent - answered, 0);

        // Gráfica 1: Enviadas vs Contestadas
        const c1 = document.getElementById('chartSentAnswered');
        if (c1) {
            this._charts.push(
                buildDoughnut(
                    c1,
                    [_t("Answered") + ` (${answered})`, _t("Unanswered") + ` (${unanswered})`],
                    [answered, unanswered],
                    ['green', 'gray']
                )
            );
        }

        // Gráfica 2: Con cumplidos
        if (d.has_compliment_indicator) {
            const withC = d.with_compliments;
            const withoutC = Math.max(answered - withC, 0);
            const c2 = document.getElementById('chartCompliments');
            if (c2) {
                this._charts.push(
                    buildDoughnut(
                        c2,
                        [_t("With Compliments") + ` (${withC})`, _t("Without Compliments") + ` (${withoutC})`],
                        [withC, withoutC],
                        ['teal', 'gray']
                    )
                );
            }
        }

        // Gráfica 3: Con quejas
        if (d.has_complaint_indicator) {
            const withQ = d.with_complaints;
            const withoutQ = Math.max(answered - withQ, 0);
            const c3 = document.getElementById('chartComplaints');
            if (c3) {
                this._charts.push(
                    buildDoughnut(
                        c3,
                        [_t("With Complaints") + ` (${withQ})`, _t("Without Complaints") + ` (${withoutQ})`],
                        [withQ, withoutQ],
                        ['red', 'gray']
                    )
                );
            }
        }

        // Gráfica 4: Positivos / Neutros / Negativos
        if (d.classification_available) {
            const c4 = document.getElementById('chartResults');
            if (c4) {
                this._charts.push(
                    buildBar(
                        c4,
                        [
                            _t("Positive") + ` (${pct(d.positive, answered)})`,
                            _t("Neutral") + ` (${pct(d.neutral, answered)})`,
                            _t("Negative") + ` (${pct(d.negative, answered)})`,
                        ],
                        [d.positive, d.neutral, d.negative],
                        'blue'
                    )
                );
            }
        }

        // Gráfica 5: Calificación máxima
        if (d.has_max_score_indicator) {
            const maxScore = d.max_score;
            const noMaxScore = Math.max(answered - maxScore, 0);
            const c5 = document.getElementById('chartMaxScore');
            if (c5) {
                this._charts.push(
                    buildDoughnut(
                        c5,
                        [_t("With Max Score") + ` (${maxScore})`, _t("Other") + ` (${noMaxScore})`],
                        [maxScore, noMaxScore],
                        ['amber', 'gray']
                    )
                );
            }
        }

    }

    _destroyCharts() {
        this._charts.forEach(ch => { try { ch.destroy(); } catch (_) { } });
        this._charts = [];
    }
}

// ── Registro ──────────────────────────────────────────────────────────────────
registry.category("actions").add("survey_audit_dashboard", SurveyAuditDashboard);

// ── Chart.js: carga dinámica si no está disponible ────────────────────────────
if (typeof Chart === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
    document.head.appendChild(script);
}
