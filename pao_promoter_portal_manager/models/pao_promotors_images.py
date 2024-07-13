from odoo import fields, models



class PaoPromotorsImages(models.Model):
    _name = 'pao.promotors.images'
    _description = 'Promotors Images'

    name = fields.Char(string="Name", default="image")
    promotor_cv_id = fields.Many2one('pao.promoter.cv',
                                     string='Promoter CV',
                                     ondelete='cascade')
    image = fields.Image(string="Carousel image", max_width=1024,
                         max_height=1024, required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company) 