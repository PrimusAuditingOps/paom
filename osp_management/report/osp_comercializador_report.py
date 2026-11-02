# -*- coding: utf-8 -*-
"""
Reporte PDF del formulario Comercializador. Igual que los demás, la
resolución de campos vive en el motor genérico compartido
(osp_report_common.py) — este archivo solo aporta el manifest propio
(COMERCIALIZADOR_REPORT_SECTIONS, ver osp_comercializador_report_data.py).
"""

from odoo import models

from .osp_comercializador_report_data import COMERCIALIZADOR_REPORT_SECTIONS


class OSPRequestComercializadorReport(models.Model):
    _inherit = 'osp.request'

    def get_comercializador_report_sections(self):
        """Devuelve la lista de secciones de Comercializador ya resuelta
        contra self.form_data. Llamado por get_report_sections()
        (osp_report_common.py)."""
        return self._resolve_report_sections(COMERCIALIZADOR_REPORT_SECTIONS)
