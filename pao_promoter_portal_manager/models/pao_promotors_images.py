from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class PaoPromotorsImages(models.Model):
    _name = 'pao.promotors.images'
    _description = 'Promotors Images'

    
    name = fields.Char(
        string="Name",
        default = "image",
    )
    promotor_cv_id = fields.Many2one(
        comodel_name='pao.promoter.cv',
        string='Promoter CV',
        ondelete='cascade',
    )
    image = fields.Image(
        string="Carousel image", 
        max_width=1024, 
        max_height=1024,
        required = True
    )
    