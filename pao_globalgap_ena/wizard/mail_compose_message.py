from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import email_normalize, email_split_and_format


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        # La notificación ENA se manda como UN solo correo (todos en "Para")
        # para que al responder no se pierda la conversación.
        if self.env.context.get('ena_single_email'):
            for wizard in self:
                wizard._ena_send_single_email()
            return {'type': 'ir.actions.act_window_close'}
        return super().action_send_mail()

    # ── Envío en un solo correo ────────────────────────────────────────────
    def _ena_get_records(self):
        self.ensure_one()
        res_ids = self._evaluate_res_ids() if hasattr(self, '_evaluate_res_ids') else False
        res_ids = res_ids or self.env.context.get('default_res_ids') or []
        return self.env['ena.solicitud'].browse(res_ids)

    def _ena_group_emails(self, record):
        """Buzones del grupo = destinatarios por defecto de la plantilla.

        Si la plantilla tiene "Responder a" (reply_to) se usa ese valor;
        si no, se usan sus destinatarios por defecto (partner_to, email_to, email_cc).
        """
        template = self.template_id or self.env.ref(
            'pao_globalgap_ena.mail_template_ena_notificacion', raise_if_not_found=False)
        if not template:
            return []

        def render(field):
            if not template[field]:
                return ''
            return template._render_field(field, [record.id])[record.id] or ''

        reply_to = render('reply_to')
        if reply_to:
            return email_split_and_format(reply_to)

        emails = []
        partner_ids = [int(pid) for pid in render('partner_to').split(',') if pid.strip().isdigit()]
        for partner in self.env['res.partner'].sudo().browse(partner_ids).exists():
            if partner.email:
                emails.append(partner.email_formatted)
        emails += email_split_and_format(render('email_to'))
        emails += email_split_and_format(render('email_cc'))
        return emails

    @staticmethod
    def _ena_dedupe(emails):
        seen, result = set(), []
        for email in emails:
            key = email_normalize(email) or email
            if key and key not in seen:
                seen.add(key)
                result.append(email)
        return result

    def _ena_send_single_email(self):
        self.ensure_one()
        for record in self._ena_get_records():
            sin_correo = self.partner_ids.filtered(lambda p: not p.email)
            if sin_correo:
                raise UserError(_('Los siguientes destinatarios no tienen correo: %s')
                                % ', '.join(sin_correo.mapped('display_name')))
            email_to = self._ena_dedupe(self.partner_ids.mapped('email_formatted'))
            if not email_to:
                raise UserError(_('Agregue al menos un destinatario.'))

            # Reply-To: buzones del grupo + alias de Odoo (si existe) para que
            # la respuesta también quede en el historial del registro.
            reply_to = self._ena_group_emails(record)
            alias = record._notify_get_reply_to(default=False).get(record.id)
            if alias:
                reply_to.append(alias)
            reply_to = self._ena_dedupe(reply_to)

            subject = self.subject or record.display_name
            body = self.body or ''

            # Se registra en el historial sin notificar a nadie por separado.
            message = record.message_post(
                body=body,
                subject=subject,
                attachment_ids=self.attachment_ids.ids,
                message_type='comment',
                subtype_xmlid='mail.mt_note',
                partner_ids=[],
            )

            mail = self.env['mail.mail'].sudo().create({
                'mail_message_id': message.id,
                'body_html': body,
                'email_to': ', '.join(email_to),
                'reply_to': ', '.join(reply_to) if reply_to else False,
                'auto_delete': True,
            })
            mail.send(raise_exception=False)

            vals = {
                'notificacion_enviada': True,
                'fecha_notificacion': fields.Date.context_today(record),
            }
            if record.stage not in ('programada', 'realizada'):
                vals['stage'] = 'notificada'
            record.write(vals)
