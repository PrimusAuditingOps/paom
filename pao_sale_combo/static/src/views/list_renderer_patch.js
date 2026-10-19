/** @odoo-module **/

import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

/**
 * Buttons inside the <control> of an x2many list ignore their `invisible` attribute in Odoo 17.
 * Evaluate it against the list context (which exposes `parent`) so a control button can be hidden,
 * e.g. "Add a combo" in the order lines, only shown for the Chilean company.
 */
patch(ListRenderer.prototype, {
    paoIsControlButtonVisible(create) {
        if (create.type !== "button" || !create.invisible) {
            return true;
        }
        return !evaluateBooleanExpr(create.invisible, this.props.list.evalContext);
    },
});
