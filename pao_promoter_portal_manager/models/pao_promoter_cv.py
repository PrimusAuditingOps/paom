from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from logging import getLogger

_logger = getLogger(__name__)
class PaoPromoterCV(models.Model):
    _name = 'pao.promoter.cv'
    _description = 'Promoter CV'

    name = fields.Char(
        string="Name",
        required=True,
    )
    company_name = fields.Char(
        string="Company",
    )
    website_published = fields.Boolean(
        string='Available on the Website', 
        copy=False,
        default = True,
    )
    profile_image = fields.Image(
        string="Profile image", 
        max_width=1024, 
        max_height=1024
    )
    company_image = fields.Image(
        string="Company image", 
        max_width=1024, 
        max_height=1024
    )
    profession = fields.Char(
        string="Profession",
        translate=True, 
    )
    work_zone_ids = fields.Many2many(
        'pao.work.zone', 
        column1='promotor_cv_id',
        column2='work_zone_id', 
        string='Work Zones',
    )
    telephone = fields.Char(
        string="Telephone",
    )
    email = fields.Char(
        string="Email",
    )
    whatsapp = fields.Char(
        string="Whatsapp",
    )
    facebook = fields.Char(
        string="Facebook",
        help="Enter URL",
    )
    instagram = fields.Char(
        string="Instagram",
        help="Enter URL",
    )
    linkedin = fields.Char(
        string="Linkedin",
        help="Enter URL",
    )
    website = fields.Char(
        string="Website",
        help="Enter URL",
    )
    promotor_description = fields.Text(
        string="Promotor Descrpcion",
        required=True,
        size=700,
        translate=True, 

    )
    about_html = fields.Html(
        'About', 
        render_engine='qweb', 
        translate=True, 
        sanitize=False
    )
    carousel_image_ids = fields.One2many(
        comodel_name='pao.promotors.images',
        inverse_name='promotor_cv_id',
        string='Carousel Images',
    )
    service_ids = fields.Many2many(
        'pao.promoter.service', 
        column1='promotor_cv_id',
        column2='service_id', 
        string='Services',
    )
    history_block_ids = fields.One2many(
        comodel_name='pao.promoter.history.block',
        inverse_name='promotor_cv_id',
        string='History',
    )

    @api.constrains('promotor_description')
    def _validate_promotor_description_size(self):
        for rec in self:
            if len(rec.promotor_description) > 700:
                raise ValidationError(_('Number of characters must not exceed 700 for the Promotor description field.'))