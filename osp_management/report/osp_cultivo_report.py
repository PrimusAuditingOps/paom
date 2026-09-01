# -*- coding: utf-8 -*-
"""
Reporte PDF del formulario Cultivo. Igual que los demás, la resolución de
campos vive en el motor genérico compartido (osp_report_common.py) — este
archivo solo aporta el manifest propio (CULTIVO_REPORT_SECTIONS, ver
osp_cultivo_report_data.py).
"""

from odoo import models

from .osp_cultivo_report_data import CULTIVO_REPORT_SECTIONS


class OSPRequestCultivoReport(models.Model):
    _inherit = 'osp.request'

    def get_cultivo_report_sections(self):
        """Devuelve la lista de secciones de Cultivo ya resuelta contra
        self.form_data. Llamado por get_report_sections()
        (osp_report_common.py)."""
        return self._resolve_report_sections(CULTIVO_REPORT_SECTIONS)
