from odoo import models, fields, api
from odoo.exceptions import ValidationError
from logging import getLogger
_logger = getLogger(__name__)

class ProductTemplateInherit(models.Model):

    _inherit = 'product.template'
    
    def copy(self, default=None):
        # Ensure default is a dictionary, if not already provided
        default = dict(default or {})
        # Set the name field to an empty string in the copied record
        default['name'] = ''
        # Call the super method with the updated default values
        return super(ProductTemplateInherit, self).copy(default)