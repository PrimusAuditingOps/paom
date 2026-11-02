# -*- coding: utf-8 -*-
"""
Migración de datos (17/ago): fuerza la recarga de las traducciones del
módulo (i18n/en_US.po, i18n/es_MX.po) con overwrite=True.

Por qué hace falta: los términos de tipo "model_terms" (texto dentro del
arch de una ir.ui.view) se re-sincronizan solos en cada actualización del
módulo, porque la vista se re-procesa por completo. Pero los términos de
tipo "model" planos —nombre de módulo (ir.module.module.shortdesc), menús
(ir.ui.menu.name), acciones (ir.actions.act_window.name), nombre de grupo
(res.groups.name), y las etiquetas de campo (ir.model.fields.field_description)—
NO se recargan automáticamente en un `-u` normal: esos registros ya existían
desde antes de que existiera el .po (creados en español, sin ninguna
traducción a inglés todavía), y Odoo por defecto no pisa una traducción
"vacía pero ya existente" salvo que se le pida explícitamente con
overwrite=True. Por eso, tras agregar los .po (17/ago), el backend seguía
en español pese a que los .po ya estaban correctos.

Este script corre una sola vez (ligado a esta versión) y llama al mismo
mecanismo interno que usa Configuración > Traducciones > Cargar una
Traducción, pero con overwrite=True para forzar la sincronización de una
vez, sin que el usuario tenga que hacerlo a mano desde la UI.
"""

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env['ir.module.module'].search([('name', '=', 'osp_management')], limit=1)
    if module:
        module._update_translations(overwrite=True)
