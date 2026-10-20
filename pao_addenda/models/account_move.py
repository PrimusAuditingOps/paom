from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Estados del CFDI en los que la factura ya está timbrada: no se exige ni se
# edita el folio (el XML ya salió con el valor que tenía).
SIGNED_CFDI_STATES = ('sent', 'cancel_requested')


class AccountMove(models.Model):
    _inherit = 'account.move'

    pao_po_number = fields.Char(
        string='Folio de orden de compra',
        copy=False,
        tracking=True,
        help='Folio de la orden de compra que entrega el cliente. '
             'Se incluye en la Addenda del CFDI.',
    )
    pao_addenda_requires_po = fields.Boolean(
        compute='_compute_pao_addenda_requires_po',
    )

    @api.depends('move_type', 'partner_id.l10n_mx_edi_addenda', 'commercial_partner_id.l10n_mx_edi_addenda')
    def _compute_pao_addenda_requires_po(self):
        addenda = self.env.ref('pao_addenda.addenda_hortifrut', raise_if_not_found=False)
        for move in self:
            # Mismo orden de búsqueda que usa l10n_mx_edi al agregar la addenda
            # al CFDI (_l10n_mx_edi_cfdi_invoice_try_send). sudo(): no todos
            # los usuarios de facturación pueden leer ir.ui.view.
            partner_addenda = (
                move.partner_id.sudo().l10n_mx_edi_addenda
                or move.commercial_partner_id.sudo().l10n_mx_edi_addenda
            )
            move.pao_addenda_requires_po = bool(
                addenda
                and move.move_type == 'out_invoice'
                and partner_addenda.id == addenda.id
            )

    def _pao_get_moves_missing_po(self):
        return self.filtered(lambda m: m.pao_addenda_requires_po and not (m.pao_po_number or '').strip())

    def _pao_po_missing_message(self):
        return _(
            "No se puede confirmar o timbrar esta factura de Hortifrut: capture el folio "
            "de la orden de compra en la pestaña Información de Addenda.\n%s",
            ', '.join(self.mapped('display_name')),
        )

    def _post(self, soft=True):
        # EXTENDS l10n_mx_edi
        # Las facturas que ya traen un CFDI timbrado (p. ej. importadas desde
        # XML) no se bloquean.
        missing = self.filtered(
            lambda m: m.l10n_mx_edi_is_cfdi_needed and m.l10n_mx_edi_cfdi_state not in SIGNED_CFDI_STATES
        )._pao_get_moves_missing_po()
        if missing:
            raise UserError(missing._pao_po_missing_message())
        return super()._post(soft=soft)

    def _l10n_mx_edi_cfdi_check_invoice_config(self):
        # EXTENDS l10n_mx_edi
        # Cubre facturas confirmadas antes de instalar el módulo: el error se
        # muestra junto a los nativos y no se envía nada al PAC.
        errors = super()._l10n_mx_edi_cfdi_check_invoice_config()
        if self._pao_get_moves_missing_po():
            errors.append(self._pao_po_missing_message())
        return errors
