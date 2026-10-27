import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# Estados del CFDI en los que la factura ya está timbrada: no se exige ni se
# edita el folio (el XML ya salió con el valor que tenía).
SIGNED_CFDI_STATES = ('sent', 'cancel_requested')

# Hortifrut solo procesa folios de exactamente 10 dígitos. [0-9] y no \d:
# \d también acepta dígitos Unicode de otros alfabetos.
PO_NUMBER_RE = re.compile(r'[0-9]{10}')


class AccountMove(models.Model):
    _inherit = 'account.move'

    pao_po_number = fields.Char(
        string='Folio de orden de compra',
        copy=False,
        tracking=True,
        help='Folio de la orden de compra que entrega el cliente (10 dígitos). '
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

    @api.constrains('pao_po_number', 'partner_id', 'move_type')
    def _check_pao_po_number(self):
        # Un folio vacío se permite al guardar; se exige al confirmar/timbrar.
        for move in self:
            if move.pao_addenda_requires_po and (move.pao_po_number or '').strip() and not move._pao_po_number_is_valid():
                raise ValidationError(_(
                    "El folio de orden de compra debe tener exactamente 10 dígitos numéricos. "
                    "Valor capturado: %s",
                    move.pao_po_number,
                ))

    def _pao_po_number_is_valid(self):
        self.ensure_one()
        return bool(PO_NUMBER_RE.fullmatch((self.pao_po_number or '').strip()))

    def _pao_get_moves_invalid_po(self):
        # Sin folio o con formato inválido (p. ej. capturado antes de existir
        # la regla de 10 dígitos).
        return self.filtered(lambda m: m.pao_addenda_requires_po and not m._pao_po_number_is_valid())

    def _pao_invalid_po_message(self):
        return _(
            "No se puede confirmar o timbrar esta factura de Hortifrut: capture el folio "
            "de la orden de compra (exactamente 10 dígitos) en la pestaña Información de Addenda.\n%s",
            ', '.join(self.mapped('display_name')),
        )

    def _post(self, soft=True):
        # EXTENDS l10n_mx_edi
        # Las facturas que ya traen un CFDI timbrado (p. ej. importadas desde
        # XML) no se bloquean.
        invalid = self.filtered(
            lambda m: m.l10n_mx_edi_is_cfdi_needed and m.l10n_mx_edi_cfdi_state not in SIGNED_CFDI_STATES
        )._pao_get_moves_invalid_po()
        if invalid:
            raise UserError(invalid._pao_invalid_po_message())
        return super()._post(soft=soft)

    def _l10n_mx_edi_cfdi_check_invoice_config(self):
        # EXTENDS l10n_mx_edi
        # Cubre facturas confirmadas antes de instalar el módulo: el error se
        # muestra junto a los nativos y no se envía nada al PAC.
        errors = super()._l10n_mx_edi_cfdi_check_invoice_config()
        if self._pao_get_moves_invalid_po():
            errors.append(self._pao_invalid_po_message())
        return errors
