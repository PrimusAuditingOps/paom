/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
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
 */
export class PaoSalesBudgetLineListController extends ListController {
    setup() {
        super.setup();
        this.busService = useService("bus_service");
        this._onBusNotification = this._onBusNotification.bind(this);

        onWillStart(() => {
            this.busService.addChannel(BUS_CHANNEL);
            this.busService.addEventListener("notification", this._onBusNotification);
        });
        onWillDestroy(() => {
            this.busService.removeEventListener("notification", this._onBusNotification);
        });
    }

    _onBusNotification({ detail: notifications }) {
        for (const { type, payload } of notifications) {
            if (type !== BUS_NOTIFICATION_TYPE) {
                continue;
            }
            this._maybeRefresh(payload);
        }
    }

    async _maybeRefresh(payload) {
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
        await this.model.load();
    }
}

export const paoSalesBudgetLineListView = {
    ...listView,
    Controller: PaoSalesBudgetLineListController,
};

registry.category("views").add("pao_sales_budget_line_list", paoSalesBudgetLineListView);
