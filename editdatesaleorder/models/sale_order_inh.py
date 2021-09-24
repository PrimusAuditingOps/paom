from odoo import api, exceptions, fields, models, _


class SaleOrderInh(models.Model):
    _inherit='sale.order'


    date_order = fields.Datetime(string='Order Date', 
    required=True, readonly=False, index=True, 
    states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
    copy=False, default=fields.Datetime.now, 
    help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")

    edso_is_date_editable = fields.Boolean(
        string="is date sale order editable",
        compute='_get_is_editable_date_sale_order',
    )

    def _get_is_editable_date_sale_order(self):
        for rec in self:
            group = self.env.ref('editdatesaleorder.edit_sale_order_date_group')
            rec.edso_is_date_editable = group.id in self.env.user.groups_id.ids