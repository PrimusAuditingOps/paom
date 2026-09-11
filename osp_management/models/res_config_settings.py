# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Llaves de Cloudflare Turnstile (verificación anti-bot de los
    # formularios públicos de OSP, sin login). Guardadas como
    # ir.config_parameter vía config_parameter= (patrón estándar de Odoo) —
    # editables desde Ajustes sin tocar código ni redesplegar. Se leen en
    # controllers/portal.py (_render_public_form y _verify_turnstile).
    # Mientras osp_turnstile_secret_key esté vacía, la verificación se omite
    # por completo (ver _verify_turnstile) — así el formulario público sigue
    # funcionando mientras el administrador termina de configurar Turnstile.
    osp_turnstile_site_key = fields.Char(
        string='Turnstile Site Key',
        config_parameter='osp_management.turnstile_site_key',
        help="Cloudflare Turnstile Site Key (público) — se usa en el HTML "
             "de los formularios públicos de OSP.")
    osp_turnstile_secret_key = fields.Char(
        string='Turnstile Secret Key',
        config_parameter='osp_management.turnstile_secret_key',
        help="Cloudflare Turnstile Secret Key (privado) — se usa server-side "
             "para verificar cada envío. Nunca se expone en el HTML.")
