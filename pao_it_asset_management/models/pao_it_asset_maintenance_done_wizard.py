from odoo import models, fields


# ==========================================
# VENTANA "MARCAR COMO TERMINADO"
# ==========================================
# Pide los datos para cerrar un mantenimiento. Existe para que el botón
# funcione igual desde la pestaña (de solo lectura) del activo, el menú o
# el calendario.
class PaoItAssetMaintenanceDoneWizard(models.TransientModel):
    _name = 'pao.it.asset.maintenance.done.wizard'
    _description = 'Finish IT Asset Maintenance'

    maintenance_id = fields.Many2one('pao.it.asset.maintenance', string='Maintenance', required=True)
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.context_today)
    condition_after_id = fields.Many2one('pao.it.condition', string='Condition After', required=True)
    work_performed = fields.Text(string='Work Performed')

    def action_confirm(self):
        self.ensure_one()
        self.maintenance_id._finish(self.end_date, self.condition_after_id, self.work_performed)
        return {'type': 'ir.actions.act_window_close'}
