# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
from werkzeug.urls import url_join


class ENALostReason(models.Model):
    _name = 'ena.lost.reason'
    _description = 'ENA Lost Reason'
    
    name = fields.Char(
        string='Motivo de no realización',
        required=True,
    )
    
    