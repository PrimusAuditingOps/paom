from odoo import fields, models, api
from datetime import *
import logging

_logger = logging.getLogger(__name__)

class ResPartnerInherit(models.Model):
    
    _inherit = "res.partner"
    
    specialist_audits_quantity = fields.Float('Number of audits to coordinate', default=0)
    ado_is_specialist = fields.Boolean('Is an Operations Specialist', default = False)

    specialist_audits_coordinated = fields.Float('Coordinated audits', readonly=True, compute="_compute_specialist_audits_number")
    specialist_goal_progress = fields.Integer('Specialist\'s progress', readonly=True, compute="_compute_specialist_goal_progress")
    specalist_audits_goal = fields.Integer('Specialist current audits goal', readonly=True, compute="_compute_specialist_number_goal")
    specialist_period_type = fields.Char('Specialist period type', readonly=True, compute="_compute_specialist_period_type")
    
    @api.depends("specialist_audits_quantity")
    def _compute_specialist_audits_number(self):
        
        for rec in self:
            
            rec.specialist_audits_coordinated=0.0
            
            if rec.ado_is_specialist:
                
                configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])
                
                if len(configuration) > 0:
                    
                    period =self._get_specialist_period_dates()
                    start_date=datetime.strptime(period[0], '%Y-%m-%d').date()
                    end_date=datetime.strptime(period[1], '%Y-%m-%d').date()
                    # counter = 0.0
                    
                    query = """
                        SELECT 
                            SUM(l.product_qty) as coordinated_audits
                        FROM
                            purchase_order pu
                                INNER JOIN purchase_order_line l ON l.order_id = pu.id
                                INNER JOIN auditconfirmation_auditstate a ON a.id = pu.ac_audit_status
                                INNER JOIN product_product p ON p.id = l.product_id
                                LEFT JOIN product_template pt ON pt.id = p.product_tmpl_id
                                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                        WHERE
                            pu.coordinator_id = %(coordinator)s AND
                            pc.paa_is_an_audit AND
                            l.service_start_date >= %(start_date)s AND
                            l.service_start_date <= %(end_date)s AND
                            a.name = 'Confirmada' AND
                            l.state <> 'cancel'
                    """
                    params = {
                        'coordinator': rec.user_ids._origin.id,
                        'start_date': start_date,
                        'end_date': end_date,
                    }
                    
                    if not params['coordinator']:
                        rec.specialist_audits_coordinated = 0
                        return
                    
                    self.env.cr.execute(query, params)
                    query_result = self.env.cr.dictfetchall()
                    
                    for row in query_result:
                        rec.specialist_audits_coordinated = (float) (row['coordinated_audits'] if row['coordinated_audits'] else 0)
                    
                    # domain = [('coordinator_id', '=', rec.user_ids.id)]
                    # purchase = self.env['purchase.order'].search(domain)
                    
                    # for pu in purchase:
                        
                    #     domain = [('order_id', '=', pu.id),('service_start_date','>=',start_date),('service_start_date','<=',end_date),('state','!=','cancel'),('ac_audit_status', '=', 'Confirmada')]
                    #     purchase_orderline = self.env['purchase.order.line'].search(domain)
                    
                    #     for r in purchase_orderline:
                    #         qty = r.product_qty
                    #         for p in r.product_id:
                    #             for c in p.categ_id:
                    #                 if c.paa_is_an_audit:
                    #                     counter+=qty
                    
                    # rec.specialist_audits_coordinated=counter
                           
                                                                
    @api.depends("specialist_audits_quantity")
    def _compute_specialist_goal_progress(self):
        
        for rec in self:
            configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])
            
            if rec.ado_is_specialist and len(configuration) > 0:
                
                audits_number = rec.specialist_audits_coordinated

                goal=rec.specalist_audits_goal
                
                progress = (audits_number/goal) if goal > 0 else 0
                rec.specialist_goal_progress= (int) (progress*100)
            else:
                rec.specialist_goal_progress = 0

    @api.depends("specialist_audits_quantity")
    def _compute_specialist_period_type(self):
        
        for rec in self:
            configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])           
            
            if rec.ado_is_specialist and len(configuration) > 0:
                period_type = rec._get_specialist_period_dates()
                start_date = period_type[0]
                end_date = period_type[1]
                pType= period_type[2]
                rec.specialist_period_type = str(pType)+"   Del  "+start_date+"  al  "+end_date
            else:
                rec.specialist_period_type = "None"

    @api.depends("specialist_audits_quantity")
    def _compute_specialist_number_goal(self):
        
        for rec in self:
            configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])
            
            if rec.ado_is_specialist and len(configuration) > 0:
                rec.specalist_audits_goal = rec.specialist_audits_quantity
            else:
                rec.specalist_audits_goal = 0

    def _get_specialist_period_dates(self):
        
        configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])
        current_date=datetime.today()
        
        current_year= current_date.year
        current_month= current_date.month
        
        init_month = ""
        init_year = ""
        end_day = ""
        end_month = ""
        end_year = ""
        period_type="Specialist"

        for con in configuration:
            
            # _logger.error("------------------ Conf N <-----------------------")

            period_month_start = int(con.season_start_month)
            period_moth_end = int(con.season_end_month)

            if period_month_start > current_month:
                init_year = current_year-1
                end_year = current_year
            elif period_month_start <= current_month:
                init_year = current_year
                end_year = current_year+1

            init_month = period_month_start
            end_month = period_moth_end

        init_day = 1
        end_day = self.number_of_days_in_month(end_year, end_month)
        start_date = str(init_year)+"-"+str(init_month)+"-"+str(init_day)
        end_date = str(end_year)+"-"+str(end_month)+"-"+str(end_day)
        return [start_date, end_date, period_type]
