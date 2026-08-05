# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import fields, models, _
from odoo.exceptions import UserError

SEND_TO_CALIDAD_ACTIVITY_SUMMARY = 'Revisar polígonos de sitios'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    site_plot_ids = fields.One2many(
        comodel_name='pao.site.plot',
        inverse_name='sale_order_id',
        string='Sitios',
    )
    site_plot_count = fields.Integer(
        string='# Sitios',
        compute='_compute_site_plot_count',
    )
    service_ids = fields.One2many(
        comodel_name='pao.site.plot.service',
        inverse_name='sale_order_id',
        string='Servicios estimados',
    )
    qa_user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Usuarios QA',
        help='Usuarios de Calidad responsables de revisar los sitios y estimar '
             'los servicios de esta cotización.',
    )

    def _compute_site_plot_count(self):
        for order in self:
            order.site_plot_count = len(order.site_plot_ids)

    def action_view_site_plots(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'pao_site_plot_survey.action_pao_site_plot'
        )
        action['domain'] = [('sale_order_id', '=', self.id)]
        action['context'] = {'default_sale_order_id': self.id}
        return action

    def _pao_pending_site_plots(self):
        self.ensure_one()
        return self.site_plot_ids.filtered(lambda s: not s.geojson_polygon)

    def _pao_calidad_mention_body(self):
        """Body with real inline @mentions (not just silent notification
        recipients), one per selected Usuario QA.

        Must be built as `Markup`, not a plain str: message_post()/the Html
        field escape plain strings, which is what previously made the raw
        `<a ...>` tag source show up as literal text in the chatter instead
        of rendering as a clickable mention.
        """
        self.ensure_one()
        mentions = [
            Markup(
                '<a href="#" data-oe-model="res.partner" data-oe-id="{}" class="o_mail_redirect">@{}</a>'
            ).format(user.partner_id.id, user.partner_id.name)
            for user in self.qa_user_ids
        ]
        mentions_html = Markup(', ').join(mentions)
        return Markup(_(
            'Se han agregado sitios a esta cotización para tu verificación y '
            'estimación de costos: %s'
        )) % mentions_html

    def action_send_sites_to_calidad(self):
        self.ensure_one()
        if not self.site_plot_ids:
            raise UserError(_('This quotation has no sites yet.'))
        if not self.qa_user_ids:
            raise UserError(_('Select at least one Usuario QA before sending the sites for review.'))
        pending = self._pao_pending_site_plots()
        if pending:
            raise UserError(
                _('These sites still have no polygon drawn: %s')
                % ', '.join(pending.mapped('name'))
            )
        self.site_plot_ids.write({'state': 'sent_to_calidad'})

        self.message_post(
            body=self._pao_calidad_mention_body(),
            partner_ids=self.qa_user_ids.partner_id.ids,
            subtype_xmlid='mail.mt_note',
        )

        activity_type = self.env.ref('mail.mail_activity_data_todo')
        for user in self.qa_user_ids:
            existing_activity = self.env['mail.activity'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', self.id),
                ('summary', '=', SEND_TO_CALIDAD_ACTIVITY_SUMMARY),
                ('user_id', '=', user.id),
            ], limit=1)
            if not existing_activity:
                self.activity_schedule(
                    activity_type_id=activity_type.id,
                    summary=SEND_TO_CALIDAD_ACTIVITY_SUMMARY,
                    note=_('Sites are ready for review on quotation %s.') % self.name,
                    user_id=user.id,
                )

    def action_export_site_plots_kml(self):
        self.ensure_one()
        if not self.site_plot_ids:
            raise UserError(_('This quotation has no sites yet.'))
        pending = self._pao_pending_site_plots()
        if pending:
            raise UserError(
                _('These sites still have no polygon drawn: %s')
                % ', '.join(pending.mapped('name'))
            )
        return self.site_plot_ids.action_export_kml()
