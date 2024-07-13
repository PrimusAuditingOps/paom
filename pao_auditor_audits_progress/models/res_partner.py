from odoo import fields, models, api
from datetime import *
from calendar import monthrange
import logging

_logger = logging.getLogger(__name__)

class RestPartnerInherit(models.Model):
    
    _inherit = "res.partner"

    audits_done = fields.Integer('Confirmed audits', readonly=True, compute="_compute_audits_number")
    progress_bar = fields.Integer('Progress', readonly=True, compute="_compute_audits_progress_bar")
    audits_goal = fields.Integer('Audits goal', readonly=True, compute="_compute_audits_number_goal")
    period_type = fields.Char('Period type', readonly=True, compute="_compute_period_type")

    @api.depends("paa_audit_quantity")
    def _compute_audits_number(self):
        
        for rec in self:
            
            configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])
            
            if rec.ado_is_auditor and len(configuration) > 0:

                period =self._get_start_and_end_period_dates()
                start_date=datetime.strptime(period[0], '%Y-%m-%d').date()
                end_date=datetime.strptime(period[1], '%Y-%m-%d').date()
                counter = 0
                domain = [('partner_id', '=', rec.id),('service_start_date','>=',start_date),('service_start_date','<=',end_date),('state','!=','cancel'),('ac_audit_status', '=', 'Confirmada')]
                purchaseordeline = self.env['purchase.order.line'].search(domain)
                
                for r in purchaseordeline:
                    qty = r.product_qty
                    for p in r.product_id:
                        for c in p.categ_id:
                            if c.paa_is_an_audit:
                                counter+=qty
                                                            
                rec.audits_done=counter
            #else: 
            #    rec.audits_done=0
            else:
                rec.audits_done=0
                        
    @api.depends("paa_audit_quantity")
    def _compute_audits_progress_bar(self):
        
        for u in self:
            configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])
            
            if u.ado_is_auditor and len(configuration) > 0:
                
                period =self._get_start_and_end_period_dates()
                start_date=datetime.strptime(period[0], '%Y-%m-%d').date()
                end_date=datetime.strptime(period[1], '%Y-%m-%d').date()
                audits_number = 0
                #audits_number = (int) (u._get_audits_number/u.audits_target)*100     
                domain = [('partner_id', '=', u.id),('service_start_date','>=',start_date),('service_start_date','<=',end_date),('state','!=','cancel'),('ac_audit_status', '=', 'Confirmada')]
                purchaseordeline = self.env['purchase.order.line'].search(domain)
                for r in purchaseordeline:
                    qty = r.product_qty
                    for p in r.product_id:
                        for c in p.categ_id:
                            if c.paa_is_an_audit:
                                audits_number+=qty

                goal=u._get_audits_number_goal()
                
                if not goal == 0:
                #progress = (int) (audits_number/u.audits_target)*100
                    progress = audits_number/goal
                    u.progress_bar= (int) (progress*100)
                else:
                    u.progress_bar = 0
            
            else:
                u.progress_bar = 0

    @api.depends("paa_audit_quantity")
    def _compute_period_type(self):
        
        for rec in self:
            configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])           
            
            if rec.ado_is_auditor and len(configuration) > 0:
                period_type = rec._get_start_and_end_period_dates()
                start_date = period_type[0]
                end_date = period_type[1]
                pType= (str(period_type[2])).upper()
                
                year1, month1, day1 = start_date.split('-')
                year2, month2, day2 = end_date.split('-')

                formatted_start_date = "{}-{:02d}-{:02d}".format(year1, int(month1), int(day1))
                formatted_end_date = "{}-{:02d}-{:02d}".format(year2, int(month2), int(day2))
                
                rec.period_type = pType + ": Desde "+ formatted_start_date +" hasta " + formatted_end_date
            else:
                rec.period_type = "None"

    @api.depends("paa_audit_quantity")
    def _compute_audits_number_goal(self):
        
        for rec in self:
            configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])
            
            if rec.ado_is_auditor and len(configuration) > 0:
                rec.audits_goal = rec._get_audits_number_goal()
            else:
                rec.audits_goal = 0

    def _get_start_and_end_period_dates(self):
        
        configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])
        #today=datetime.strptime("2022-09-01", '%Y-%m-%d').date()
        today=datetime.today()
        anio= today.year
        mes= today.month
        diaInicial = ""
        mesInicial = ""
        anioInicial = ""
        diaFinal = ""
        mesFinal = ""
        anioFinal = ""
        tipoPeriodo=""

        for con in configuration:

            ms = int(con.season_start_month)
            me = int(con.season_end_month)

            if con.option == "auditor":

                if ms > mes:
                    anioInicial= anio-1
                    anioFinal= anio
                elif ms <= mes:
                    anioInicial= anio
                    anioFinal= anio+1

                mesInicial = ms
                mesFinal = me

                tipoPeriodo= "Auditor"

            elif con.option == "month":
                
                for month in con.audits_quantity_per_month_ids:
                    ms = int(month.month)
                    if ms == mes:
                        anioInicial= anio
                        mesInicial = mes
                        anioFinal = anio
                        mesFinal = mes

                tipoPeriodo= "Mes"

            elif con.option == "trimester":
                
                anioInicioTemporada=""

                if ms > mes:
                    anioInicioTemporada= anio-1
                elif ms <= mes:
                    anioInicioTemporada= anio

                #Quarter actual de temporada [añoInicio , mesInicio, añoFin , mesFin, numeroQuarter] 
                currentQuarter = self._get__current_quarter_dates_of_the_season(anioInicioTemporada,ms)
                anioInicial= currentQuarter[0]
                mesInicial = currentQuarter[1]
                anioFinal = currentQuarter[2]
                mesFinal = currentQuarter[3]
                _logger.error("------------------ Current Quarter  > "+str(currentQuarter)+" <-----------------------")
                
                tipoPeriodo= "Trimestre"

            elif con.option == "season":

                if ms > mes:
                    anioInicial= anio-1
                    anioFinal= anio
                elif ms <= mes:
                    anioInicial= anio
                    anioFinal= anio+1

                mesInicial = ms
                mesFinal = me

                tipoPeriodo= "Temporada"

        diaInicial = 1
        diaFinal = self.number_of_days_in_month(anioFinal, mesFinal)
        start_date = str(anioInicial)+"-"+str(mesInicial)+"-"+str(diaInicial)
        end_date = str(anioFinal)+"-"+str(mesFinal)+"-"+str(diaFinal)
        return [start_date, end_date, tipoPeriodo]
    
    def _get__current_quarter_dates_of_the_season(self, anioInicialTemporada, mesInicialTemporada):
        
        today=datetime.today()
        aIQ=anioInicialTemporada
        mIQ= mesInicialTemporada
        aFQ= aIQ + 1 if mIQ + 2 >12 else aIQ
        mFQ=mIQ-10 if mIQ + 2 > 12 else mIQ+2
        quarterNumber=1

        isThisQuarter=False

        try:
            while not isThisQuarter:

                if today.month >= mIQ and today.month <= mFQ and today.year == aIQ and today.year==aFQ:
                    isThisQuarter= True
                    _logger.error("--------SUCCESS - TIPO DE PERIODO 1--------------------")
                elif today.month < mIQ and today.month <= mFQ and today.year > aIQ and today.year==aFQ:
                    isThisQuarter= True
                    _logger.error("--------SUCCESS - TIPO DE PERIODO 2--------------------")

                elif today.month >= mIQ and today.month > mFQ and today.year == aIQ and today.year<aFQ:
                    isThisQuarter= True
                    _logger.error("--------SUCCESS - TIPO DE PERIODO 3--------------------")

                else:
                    aIQ= aIQ+1 if mIQ+3>12 else aIQ
                    mIQ= mIQ-9 if mIQ + 3 > 12 else mIQ+3
                    aFQ= aFQ + 1 if mFQ + 3 >12 else aFQ
                    mFQ=mFQ-9 if mFQ + 3 > 12 else mFQ+3
                    quarterNumber+=1
        
        except Exception as e:
            _logger.error("------------------An exception occurred >"+str(e)+"-----------------------")
            

        #Fechas de inicio y fin del trimestre actual [ añoInicio , mesInicio, añoFin , mesFin, numeroCuadrante] 
        return [aIQ, mIQ, aFQ, mFQ, quarterNumber]

    def _get_audits_number_goal(self):

        configuration = self.env['paoassignmentauditor.configuration.audit.quantity'].search([])
        today=datetime.today()
        anio= today.year
        mes= today.month
        audit_number_goal=0

        for con in configuration:

            ms = int(con.season_start_month)

            if con.option == "auditor":
                for rec in self:
                    audit_number_goal= rec.paa_audit_quantity

            elif con.option == "month":
                for month in con.audits_quantity_per_month_ids:
                    ms = int(month.month)
                    if ms == mes:
                        audit_number_goal= month.audit_quantity
                        

            elif con.option == "trimester":
                
                anioInicioTemporada=""

                if ms > mes:
                    anioInicioTemporada= anio-1
                elif ms <= mes:
                    anioInicioTemporada= anio

                #Quarter actual de temporada [añoInicio , mesInicio, añoFin , mesFin, numeroQua] 
                currentQuarter = self._get__current_quarter_dates_of_the_season(anioInicioTemporada,ms)
                cuarterNumber = currentQuarter[4]
                #_logger.error("------------------ Current Quarter Number > "+str(cuarterNumber)+" <-----------------------")
                
                if cuarterNumber == 1:
                    audit_number_goal=con.first_month_audit_quantity
                    
                elif cuarterNumber == 2:
                    audit_number_goal=con.second_month_audit_quantity

                elif cuarterNumber == 3:
                    audit_number_goal=con.third_month_audit_quantity
            
                elif cuarterNumber == 4:
                    audit_number_goal=con.fourth_month_audit_quantity

            elif con.option == "season":

                audit_number_goal=con.audit_quantity

            _logger.error("------------------ Current Audit Goal > "+str(audit_number_goal)+" <-----------------------")
                
        return audit_number_goal
        
    def number_of_days_in_month(self, year, month):
        return monthrange(year, month)[1]
