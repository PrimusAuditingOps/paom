# -*- coding: utf-8 -*-
# © <2020> <otorresmx (otorres@proogeeks.com)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api

class FleetVehicleInh(models.Model):
    _inherit = 'fleet.vehicle'

    number_vehicle = fields.Char(
        string='Vehicle Number'
    )