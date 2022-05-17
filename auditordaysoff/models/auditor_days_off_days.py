from turtle import title
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class AuditorDaysOffDays(models.Model):
    
    _name = 'auditordaysoff.days'
    _description = 'Days off for the auditors'

    name = fields.Char(
        required=True,
        string= "name",
    )
    auditor_id = fields.Many2one(
        string="Auditor",
        comodel_name='res.partner',
        ondelete='cascade',
        required=True,
        index=True,
        domain = [('ado_is_auditor','=',True)],
    )
    all_day = fields.Boolean(
        string="All Day",
        default=True,
    )
    start_date = fields.Date(
         string="Start date",
         required=True,
    )
    end_date = fields.Date(
         string="End date",
         required=True,
    )
    comments = fields.Text(
        string="Comments"
    )
    @api.onchange('start_date','auditor_id')
    def _change_auditor_id_start_date(self):
        for rec in self:
            if rec.auditor_id and rec.start_date and rec.end_date:
                domain = [('partner_id', '=', rec.auditor_id.id),
                            ('state', '<>', 'cancel'),
                            '|','|','|',
                            '&',('service_start_date', '>=', rec.start_date),
                            ('service_start_date', '<=', rec.end_date),
                            '&',('service_end_date', '<=', rec.start_date),
                            ('service_end_date', '>=', rec.end_date),
                            '&',('service_start_date', '<=', rec.start_date),
                            ('service_end_date', '>=', rec.start_date),
                            '&',('service_start_date', '<=', rec.end_date),
                            ('service_end_date', '>=', rec.end_date)
                            ]
                recordpurchasline = self.env['purchase.order.line'].search(domain)
                if recordpurchasline:
                    rec.start_date = None
                    rec.end_date = None
                    msg = _('The auditor contains Purchase Orders on the selected dates.')
                    title_msg = _("Auditor's days off")
                    return {
                        'warning': {
                            'title': title_msg,
                            'message': msg,
                        },
                    }   
    
    @api.constrains('end_date')
    def _validate_auditor_dates(self):
        for rec in self:
            domain = [('partner_id', '=', rec.auditor_id.id),
                ('state', '<>', 'cancel'),
                '|','|','|',
                '&',('service_start_date', '>=', rec.start_date),
                ('service_start_date', '<=', rec.end_date),
                '&',('service_end_date', '<=', rec.start_date),
                ('service_end_date', '>=', rec.end_date),
                '&',('service_start_date', '<=', rec.start_date),
                ('service_end_date', '>=', rec.start_date),
                '&',('service_start_date', '<=', rec.end_date),
                ('service_end_date', '>=', rec.end_date)
                ]
            recordpurchasline = self.env['purchase.order.line'].search(domain)
            if recordpurchasline:
                msg = _('The auditor contains Purchase Orders on the selected dates.')
                raise ValidationError(msg)