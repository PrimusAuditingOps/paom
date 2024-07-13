from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from logging import getLogger

_logger = getLogger(__name__)



class PaaAuditorQualificationTop(models.Model):
    _name = 'paoassignmentauditor.auditor.qualification.top'
    _description = 'Auditor assignment Qualification Top'
    _rec_name = 'auditor_id'
    _order = 'qualification desc'

    auditor_id = fields.Many2one('res.partner', string='Auditor', ondelete='set null')
    position = fields.Integer(string='Position')
    qualification = fields.Float(default=0.00, required=True, string="Qualification")
    ref_user_id = fields.Integer(string='User ID')
    order_id = fields.Many2one('purchase.order',
                                  string="Purchase Order",
                                  ondelete='cascade')
    