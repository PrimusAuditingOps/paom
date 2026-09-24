from odoo import models, fields


# ==========================================
# GALERÍA DEL ACTIVO
# ==========================================
# Fotos de evidencia (estado al recibir, daños, etc.) que se muestran como
# mosaico en la pestaña "Gallery" de la ficha. Las fotos de un mantenimiento
# NO se copian aquí: se quedan en su propio mantenimiento (entregable 3).
class PaoItAssetImage(models.Model):
    _name = 'pao.it.asset.image'
    _description = 'IT Asset Photo'
    _inherit = ['image.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Title', required=True)
    asset_id = fields.Many2one('pao.it.asset', string='Asset', required=True, ondelete='cascade',
                               index=True)
    company_id = fields.Many2one(related='asset_id.company_id', store=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    description = fields.Text(string='Description')
    image_1920 = fields.Image(required=True)
