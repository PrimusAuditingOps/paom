from odoo import fields, models

class PurchaseReportInherit(models.Model):
    _inherit = "purchase.report"
    
    cgg_group_id = fields.Many2one(
        'customergroups.group', 
        string='Group', 
        readonly=True
    )

    promotor_id = fields.Many2one(
        'comisionpromotores.promotor', 
        string='Promoter', 
        readonly=True
    )
    
    def _select(self):
        return super(PurchaseReportInherit, self)._select() + ", rp.promotor_id as promotor_id, rp.cgg_group_id as cgg_group_id"

    def _from(self):
        return super(PurchaseReportInherit, self)._from() + """ left join sale_order saleord on (saleord.id=po.sale_order_id) 
        left join res_partner rp on (rp.id=saleord.partner_id)
        left join customergroups_group cg on (cg.id=rp.cgg_group_id) 
        left join comisionpromotores_promotor prom on (prom.id=rp.promotor_id) """

    def _group_by(self):
        if super(PurchaseReportInherit, self)._group_by().find(".effective_date") > -1:
            return super(PurchaseReportInherit, self)._group_by() + ", rp.promotor_id, rp.cgg_group_id"
        else:
            return super(PurchaseReportInherit, self)._group_by().replace("effective_date", "po.effective_date") + ", rp.promotor_id, rp.cgg_group_id"

   