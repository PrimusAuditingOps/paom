/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

// ============================================================
// Client action que incrusta, dentro del backend de Odoo (mismo
// top menu / breadcrumbs), el formulario web real que llena el
// cliente en el portal. Se reutiliza tal cual — sin duplicar los
// ~300 campos/12 tablas — por lo que el admin ve exactamente las
// mismas capturas que el cliente, y el guardado usa el mismo
// endpoint /my/osp/save/<id> (sincronización garantizada).
// Ver CONTEXT.md, punto 6, para la decisión de arquitectura.
// ============================================================
class OspAdminFormView extends Component {
    static template = "osp_management.OspAdminFormView";

    get iframeUrl() {
        const params = this.props.action.params || {};
        return `/my/osp/form/${params.osp_id}`;
    }
}

registry.category("actions").add("osp_admin_form_view", OspAdminFormView);
