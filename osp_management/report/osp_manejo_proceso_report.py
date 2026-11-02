# -*- coding: utf-8 -*-
"""
Reporte PDF del formulario Manejo o Proceso. Igual que los demás, la
resolución de campos vive en el motor genérico compartido
(osp_report_common.py) — este archivo solo aporta el manifest propio
(MANEJO_PROCESO_REPORT_SECTIONS, ver osp_manejo_proceso_report_data.py).
"""

from odoo import models

from .osp_manejo_proceso_report_data import MANEJO_PROCESO_REPORT_SECTIONS


class OSPRequestManejoProcesoReport(models.Model):
    _inherit = 'osp.request'

    def get_manejo_proceso_report_sections(self):
        """Devuelve la lista de secciones de Manejo o Proceso ya resuelta
        contra self.form_data. Llamado por get_report_sections()
        (osp_report_common.py)."""
        return self._resolve_report_sections(MANEJO_PROCESO_REPORT_SECTIONS)
