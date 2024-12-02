from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class ResPartner(models.Model):

    _inherit='res.partner'
    

    pao_current_customer = fields.Selection(
        selection=[
            ('no', "No"),
            ('yes', "Yes"),
            ('returning', "Returning"),
        ],
        string="Current customer", 
        copy=False,
        default='no',
    )
    
    pao_previous_cb_id = fields.Many2one(
        comodel_name = 'pao.cr.cb', 
        string='Previous CB', 
        help='Select CB', 
        ondelete='restrict',
    )

    pao_new_cb_id = fields.Many2one(
        comodel_name = 'pao.cr.cb', 
        string='New CB', 
        help='Select CB', 
        ondelete='restrict',
    )


    