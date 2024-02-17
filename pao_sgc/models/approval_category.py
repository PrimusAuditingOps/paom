from odoo import models, fields


class ApprovalCategoryInherit(models.Model):
    _inherit = 'approval.category'
    
    internal_name = fields.Char('Internal Name', readonly=True)
                    
