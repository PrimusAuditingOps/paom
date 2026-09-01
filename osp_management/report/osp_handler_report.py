# -*- coding: utf-8 -*-
"""
Reporte PDF del formulario Handler. Igual que Crop, la resolución de
campos vive en el motor genérico compartido (osp_report_common.py) — este
archivo solo aporta el manifest propio de Handler (HANDLER_REPORT_SECTIONS,
ver osp_handler_report_data.py).
"""

from odoo import models

from .osp_handler_report_data import HANDLER_REPORT_SECTIONS


class OSPRequestHandlerReport(models.Model):
    _inherit = 'osp.request'

    def get_handler_report_sections(self):
        """Devuelve la lista de secciones de Handler ya resuelta contra
        self.form_data. Llamado por get_report_sections() (osp_report_common.py)."""
        return self._resolve_report_sections(HANDLER_REPORT_SECTIONS)
