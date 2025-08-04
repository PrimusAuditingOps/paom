from odoo import fields, models



class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    
    pao_quotation_consultant_id = fields.Many2one('comisionpromotores.promotor',
                                      string='Quotation Consultant',
                                      readonly=True)
   
    def _select(self):
        return super(PurchaseReport, self)._select() + ", saleorder.pao_promotor_id as pao_quotation_consultant_id"

   

    def _group_by(self):
        if super(PurchaseReport, self)._group_by().find(".effective_date") > -1:
            return super(PurchaseReport, self)._group_by() + ", saleorder.pao_promotor_id"
        else:
            return super(PurchaseReport, self)._group_by().replace("effective_date", "po.effective_date") + ", saleorder.pao_promotor_id"

    