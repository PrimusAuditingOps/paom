# -*- coding: utf-8 -*-
"""
Reporte PDF del formulario Crop. La lógica de resolución de campos vive en
el motor genérico compartido (osp_report_common.py, ver
_resolve_report_sections) — este archivo solo aporta el manifest propio de
Crop (CROP_REPORT_SECTIONS, ver osp_crop_report_data.py).
"""

from odoo import models

from .osp_crop_report_data import CROP_REPORT_SECTIONS


class OSPRequestCropReport(models.Model):
    _inherit = 'osp.request'

    def get_crop_report_sections(self):
        """Devuelve la lista de secciones de Crop ya resuelta contra
        self.form_data, lista para que el template QWeb del reporte solo
        la recorra. Llamado por get_report_sections() (osp_report_common.py)."""
        return self._resolve_report_sections(CROP_REPORT_SECTIONS)
