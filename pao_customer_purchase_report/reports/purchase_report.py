from odoo import fields, models



class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    
    pao_customer_id = fields.Many2one('res.partner',
                                      string='Invoice Customer',
                                      readonly=True)
    pao_crm_team_id = fields.Many2one('crm.team',
                                      string='Sales Team',
                                      readonly=True)

    def _select(self):
        return super(PurchaseReport, self)._select() + ", saleorder.partner_id as pao_customer_id, so_partner.team_id as pao_crm_team_id"

    def _from(self):
        return super(PurchaseReport, self)._from() + """ left join sale_order saleorder on (saleorder.id=po.sale_order_id) 
        left join res_partner so_partner on (so_partner.id=saleorder.partner_id)
        left join crm_team ct on (ct.id=so_partner.team_id) """

    def _group_by(self):
        if super(PurchaseReport, self)._group_by().find(".effective_date") > -1:
            return super(PurchaseReport, self)._group_by() + ", saleorder.partner_id, so_partner.team_id"
        else:
            return super(PurchaseReport, self)._group_by().replace("effective_date", "po.effective_date") + ", saleorder.partner_id, so_partner.team_id"

    
    #crm_team_id= fields.Many2one(string="Equipo de Ventas",comodel_name="crm.team", readonly=True)

    """
    def _select(self):
        return super(PurchaseReport, self)._select() + ", so.partner_id as customer_id"#, c.team_id as crm_team_id"
   
    def _from(self):
        return super(PurchaseReport, self)._from()+ left join sale_order so on (so.id=po.sale_order_id)
        #LEFT JOIN res_partner c on (c.id=so.partner_id)
        #LEFT JOIN crm_team st on (st.id=c.team_id)
    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ", so.partner_id"#, c.team_id"

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        
        fields['customer_id'] = ", so.partner_id as customer_id"
        from_clause+= ' left join sale_order so on (so.id=po.sale_order_id)'
        groupby += ', so.partner_id'
        return super(PurchaseReport, self)._query(with_clause, fields, groupby, from_clause)
    """