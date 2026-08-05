# -*- coding: utf-8 -*-
from datetime import date, datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EnaLostReasonWizard(models.TransientModel):
    _name = 'ena.lost.reason.wizard'
    _description = 'No realizado Wizard'

    name = fields.Many2one(
        comodel_name='ena.lost.reason',
        string='Motivo de no realización',
        required=True,
    )
    comments = fields.Char(
        string='comentarios'
    )

    ena_id = fields.Many2one(
        comodel_name='ena.solicitud',
        string='Auditoría no anunciada',
        ondelete='cascade',
        required=True,
    )

    def action_lost_reason(self):
        self.ensure_one()

        self.ena_id.stage = 'no_realizada'
        self.ena_id.lost_reason_id = self.name
        self.ena_id.comments = self.comments
