from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .pao_it_asset_letter import LETTER_LANGS


# ==========================================
# GENERAR RESPONSIVA DE ACTIVOS YA ASIGNADOS
# ==========================================
# Para activos que ya están asignados a un empleado y no tienen carta (p. ej.
# después de la carga inicial). Las cartas de movimientos nuevos se generan
# desde el propio asistente de movimientos.
class PaoItAssetLetterWizard(models.TransientModel):
    _name = 'pao.it.asset.letter.wizard'
    _description = 'Generate IT Asset Delivery Letter'

    asset_ids = fields.Many2many('pao.it.asset', string='Assets', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', compute='_compute_employee_id')
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    lang = fields.Selection(LETTER_LANGS, string='Language', required=True,
                            default=lambda self: 'es_MX' if (self.env.lang or '').startswith('es') else 'en_US')

    @api.depends('asset_ids')
    def _compute_employee_id(self):
        for wizard in self:
            wizard.employee_id = wizard.asset_ids.employee_id[:1]

    def action_confirm(self):
        self.ensure_one()
        employees = self.asset_ids.employee_id
        if len(employees) != 1 or self.asset_ids.filtered(lambda a: a.employee_id != employees):
            raise UserError(_("Select assets assigned to one and the same employee."))
        movements = self.env['pao.it.asset.movement']
        for asset in self.asset_ids:
            movements |= asset._get_last_movement(('assign', 'reassign'))
        letter = self.env['pao.it.asset.letter']._create_letter(
            'delivery', employees, self.asset_ids, self.date, self.lang, movements)
        action = self.env.ref('pao_it_asset_management.action_report_asset_letter').report_action(letter)
        action['close_on_report_download'] = True
        return action
