from datetime import datetime, timedelta
from odoo import fields, models, api, SUPERUSER_ID, _
from logging import getLogger
from odoo.exceptions import ValidationError

_logger = getLogger(__name__)
class SaleOrder(models.Model):

    _inherit='sale.order'
    
    pao_is_a_master_sales_order = fields.Boolean(
        string= "Is a master sales order",
        default= False,
        copy= False,
    )
    pao_is_a_child_sales_order = fields.Boolean(
        string= "Is a child sales order",
        default= False,
        copy= False,
    )
    pao_child_ids = fields.One2many('sale.order', 'pao_parent_id', string='Child Sales Order')
    pao_parent_id = fields.Many2one('sale.order', string='Master Sales Order', readonly=True, index=True)

    pao_is_parent_id_locked = fields.Boolean(
        related='pao_parent_id.locked',
        string='Is master order locked', 
        readonly=True,
        store=True,
    )



    pao_children_orders_count = fields.Integer(
        compute='_get_children_orders_count'
    )

    @api.depends('pao_child_ids')
    def _get_children_orders_count(self):
        for order in self:
            order.pao_children_orders_count = len(order.pao_child_ids)



    def action_conver_to_master(self):
        _logger.error("entro a convertir")
        self.ensure_one()
        if self.pricelist_id.pao_is_a_shared_cost_list == True:
            self.write({'pao_is_a_master_sales_order': True})
        else:
            raise ValidationError(_("To convert a quotation to a MO, a Tier4 pricing list has to be selected.")) 
    
    def action_view_children_orders(self):
        self.ensure_one()   
        ids = [r['id'] for r in self.pao_child_ids]
        action = {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _("Children orders"),
            'domain': [('id', 'in', ids)],
        }
        return action
    

    def write(self, vals):
        if self.pao_is_a_master_sales_order and vals.get('state'):
            if vals.get('state') == "cancel" and len(self.pao_child_ids.filtered_domain([('state', '!=', 'cancel')])) > 0:
                raise ValidationError(_("The MO can't be canceled because it has active child orders."))
            elif vals.get('state') not in ("draft", "cancel"):
                raise ValidationError(_("The master order status can't be changed."))
        if self.pao_is_a_child_sales_order and self.pao_parent_id.locked and vals.get('order_line'):
            raise ValidationError(_("You cannot modify this suborder because its master order is locked."))
            
        result = super(SaleOrder, self).write(vals)
        return result
    
    def action_master_order_lock(self):
        for order in self:
            order.locked = True 

   