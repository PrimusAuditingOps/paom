from odoo import models, fields, tools

class SAReport(models.Model):

    _name="sa.report"
    _description = 'Service Agreement Report'
    _auto = False
    _rec_name = 'service_registry_number'
    _order = 'service_start_date desc'
            
    id = fields.Integer("ID", readonly=True)
    quantity = fields.Integer('Quantity', readonly=True)
    organization = fields.Many2one('servicereferralagreement.organization', 'Organization', readonly=True)
    coordinator_id = fields.Many2one('res.users', 'Coordinator', readonly=True)
    service_registry_number = fields.Many2one('servicereferralagreement.registrynumber', 'Service Registry Number', readonly=True)
    sa_request_id = fields.Many2one('pao.sign.sa.agreements.sent', 'SA Request', readonly=True)
    state_id = fields.Many2one('res.country.state', 'State', readonly=True)
    sale_order_id = fields.Many2one('sale.order', 'Sale Order', readonly=True)
    service_start_date = fields.Date('Service Start Date', readonly=True)
    service_end_date = fields.Date('Service End Date', readonly=True)
        
    def _select(self, fields=None):
        if not fields:
            fields = {}
        select_ = """
            s.id as id,
            1 as quantity,
            s.organization_id as organization,
            p.create_uid as coordinator_id,
            r.state_id as state_id,
            s.id as service_registry_number,
            o.id as sale_order_id,
            p.id as sa_request_id, 
            l.service_start_date as service_start_date,
            l.service_end_date as service_end_date
        """

        for field in fields.values():
            select_ += field
        return select_

    def _from(self, from_clause=''):
        from_ = """
                servicereferralagreement_registrynumber s
                    INNER JOIN servicereferralagreement_organization r ON (r.id = s.organization_id)
                    INNER JOIN agreements_sent_registration_numbers_rel a ON (s.id = a.registration_numbers_id)
                    INNER JOIN pao_sign_sa_agreements_sent p ON (p.id = a.agreements_sent_id)
                    INNER JOIN sale_order o ON o.id = (p.sale_order_id)
                    INNER JOIN sale_order_line l ON (l.order_id = o.id AND l.registrynumber_id = s.id)
                %s
        """ % from_clause
        return from_

    def _group_by(self, groupby=''):
        groupby_ = """
            s.id,
            quantity,
            s.organization_id,
            p.id,
            o.id,
            p.create_uid,
            r.state_id,
            l.service_start_date,
            l.service_end_date %s
        """ % (groupby)
        return groupby_

    def _select_additional_fields(self, fields):
        """Hook to return additional fields SQL specification for select part of the table query.

        :param dict fields: additional fields info provided by _query overrides (old API), prefer overriding
            _select_additional_fields instead.
        :returns: mapping field -> SQL computation of the field
        :rtype: dict
        """
        return fields

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        sale_report_fields = self._select_additional_fields(fields)
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        return '%s (SELECT %s FROM %s WHERE o.state <> \'cancel\' AND document_status IN (\'sent\', \'sign\') GROUP BY %s)' % \
                (with_, self._select(sale_report_fields), self._from(from_clause), self._group_by(groupby))

    def init(self):
        # self._table = 'sa_report'
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query())) 
    
    
    ####### FINAL QUERY #######
    #
    # SELECT
    #   s.id as id,
    #   1 as quantity, 
    #   s.organization_id as organization,
    #   p.create_uid as coordinator_id,
    #   r.state_id as state_id,
    #   s.id as service_registry_number,
    #   o.id as sale_order_id,
    #   p.id as sa_request_id, 
    #   l.service_start_date as service_start_date,
    #   l.service_end_date as service_end_date
    # FROM 
    #   servicereferralagreement_registrynumber s
    #     INNER JOIN servicereferralagreement_organization r ON (r.id = s.organization_id)
    #     INNER JOIN agreements_sent_registration_numbers_rel a ON (s.id = a.registration_numbers_id)
    #     INNER JOIN pao_sign_sa_agreements_sent p ON (p.id = a.agreements_sent_id)
    #     INNER JOIN sale_order o ON o.id = (p.sale_order_id)
    #     INNER JOIN sale_order_line l ON (l.order_id = o.id AND l.registrynumber_id = s.id)
    # WHERE 
    #   o.state <> 'cancel' AND 
    #   document_status IN ('sent', 'sign') 
    # GROUP BY
    #   s.id,
    #   quantity,
    #   s.organization_id,
    #   p.id,
    #   o.id,
    #   p.create_uid,
    #   r.state_id,
    #   l.service_start_date,
    #   l.service_end_date
    #
    ###########################
