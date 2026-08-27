/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { onWillStart, onWillDestroy } from "@odoo/owl";

const BUS_CHANNEL = "pao_sales_budget_line";
const BUS_NOTIFICATION_TYPE = "pao_sales_budget_line/changed";

/**
 * Lista reactiva para pao.sales.budget.line: cuando otro usuario crea,
 * edita o borra una línea de presupuesto, todos los que tengan esta misma
 * lista abierta la ven actualizarse sola, sin refrescar la página.
 *
 * Si el usuario local está en ese momento editando una fila (typing), se
 * omite el refresco automático para no perder lo que está escribiendo; se
 * refrescará en el siguiente evento una vez que termine de editar.
 *
 * NOTA: bus_service se toma directo de env.services (no vía useService),
 * porque bus_service declara `async: true` (no una lista de métodos) y el
 * wrapper genérico de useService() revienta con ese caso ("methods is not
 * iterable"). Así es como lo consume el propio código core de Odoo, ej.
 * account_online_synchronization/.../refresh_spin_journal_widget.js.
 */
export class PaoSalesBudgetLineListController extends ListController {
    setup() {
        super.setup();
        this.busService = this.env.services.bus_service;
        this._isDestroyed = false;

        onWillStart(() => this.busService.addChannel(BUS_CHANNEL));

        // bus_service (en esta versión de Odoo) no expone un método para
        // des-suscribir un callback puntual, así que la suscripción se
        // queda viva mientras la pestaña siga abierta aunque este
        // controller ya se haya destruido (navegaste a otra vista). Por
        // eso _maybeRefresh siempre revisa _isDestroyed antes de tocar
        // el modelo, en vez de depender de cortar la suscripción.
        this.busService.subscribe(BUS_NOTIFICATION_TYPE, (payload) => this._maybeRefresh(payload));

        onWillDestroy(() => {
            this._isDestroyed = true;
            this.busService.deleteChannel(BUS_CHANNEL);
        });
    }

    async _maybeRefresh(payload) {
        if (this._isDestroyed) {
            return;
        }
        const root = this.model.root;
        // No interrumpir a un usuario que está escribiendo en una fila de
        // esta misma lista ahora mismo; se refrescará más tarde.
        if (root.editedRecord) {
            return;
        }
        // Si esta lista está acotada a un presupuesto específico (contexto
        // default_budget_id, como cuando se entra desde la ficha del
        // presupuesto) y el cambio es de otro presupuesto, se ignora.
        const currentBudgetId = this.props.context && this.props.context.default_budget_id;
        if (currentBudgetId && payload.budget_id && currentBudgetId !== payload.budget_id) {
            return;
        }
        try {
            await this.model.load();
        } catch (e) {
            // Respaldo por si el componente se destruyó justo durante el
            // load (entre el chequeo de arriba y el await).
            if (this._isDestroyed || (e && e.message === "Component is destroyed")) {
                return;
            }
            throw e;
        }
    }
}

export const paoSalesBudgetLineListView = {
    ...listView,
    Controller: PaoSalesBudgetLineListController,
};

registry.category("views").add("pao_sales_budget_line_list", paoSalesBudgetLineListView);
