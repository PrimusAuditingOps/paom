# -*- coding: utf-8 -*-
"""
Catálogo, por formulario, de las casillas "Attach ..."/"Adjunte ..."
(sufijo de campo `_attachment_needed`, ícono de clip 📎 en el HTML) que el
cliente puede marcar a lo largo del formulario para indicar que va a subir
un documento de soporte para esa pregunta específica.

Se usa SOLO del lado del servidor, para construir el checklist de
recordatorio en la pantalla pública de "Thank you" (después del Submit,
cuando ya no hay formulario vivo que leer directo del DOM — ver
_get_pending_attachment_checklist() en osp_request.py). El equivalente en
el formulario vivo (portal, o público antes de enviar) se genera 100% en
el navegador leyendo las casillas marcadas directo del DOM (ver
initAttachmentChecklist() en static/src/js/osp_form.js) — no depende de
este catálogo, así que si el texto de una casilla cambia en el XML, hay
que actualizarlo aquí también para que la pantalla de "Thank you" no quede
desactualizada.

Cada entrada: (field_key, texto tal como aparece junto al ícono de clip).
"""


ATTACHMENT_MARKERS = {
    'form_crop': [
        ('1l_certificate_attachment_needed', 'Attach a copy of your current State certificate.'),
        ('2a_documentation_attachment_needed', 'Provide all documentation.'),
        ('2b_certificate_attachment_needed', 'Attach a copy of your current organic certificate.'),
        ('2c_certificate_attachment_needed', 'Attach a copy of your previous organic certificate.'),
        ('2d_documentation_attachment_needed', 'Attach documentation that verified non-compliances have been addressed.'),
        ('5b_supply_chain_attachment_needed', 'Attach the Master Supply Chain and Product List document.'),
        ('6n_test_results_attachment_needed', 'Attach residue analysis and/or salinity test results, if applicable.'),
        ('7b_statements_attachment_needed', 'Submit signed statements from the previous land management owner stating use and all inputs applied during the previous 3 years.'),
        ('8a_seeds_attachment_needed', 'Submit supporting documents for the seeds listed above.'),
        ('9d_test_results_attachment_needed', 'Attach copies of available test results.'),
        ('9k_documentation_attachment_needed', 'If you grow crops for human consumption and use raw manure, submit supporting documentation (crop type, field ID, date manure applied, expected harvest date).'),
        ('9o_analysis_attachment_needed', 'Attach residue analysis/additive specifications for manure, if available.'),
        ('15a_diagrams_attachment_needed', 'Attach a flow chart and a floor plan.'),
        ('15e_evidence_attachment_needed', 'Attach documented evidence.'),
        ('15r_label_attachment_needed', 'Attach label.'),
        ('15s_test_kit_attachment_needed', 'If chlorine levels are monitored, attach a label or spec sheet of the test kit used.'),
        ('16e_supporting_document_attachment_needed', 'You may submit a supporting document with a list.'),
        ('16k_documents_attachment_needed', 'Submit the documents listed above.'),
        ('19_certification_attachment_needed', 'Submit a copy of your certification (table below not required).'),
    ],
    'form_handler': [
        ('1l_certificate_attachment_needed', 'Attach a copy of your current State certificate.'),
        ('2a_documentation_attachment_needed', 'Provide all documentation.'),
        ('2b_certificate_attachment_needed', 'Attach a copy of your current organic certificate.'),
        ('2c_certificate_attachment_needed', 'Attach a copy of your previous organic certificate.'),
        ('2d_documentation_attachment_needed', 'Attach documentation that verified non-compliances have been addressed.'),
        ('4g_ingredients_list_attachment_needed', 'Submit a list of the ingredients used and for each one indicate whether it is of organic origin.'),
        ('5b_supply_chain_attachment_needed', 'Attach the Master Supply Chain and Product List document.'),
        ('6i_results_attachment_needed', 'Attach the results from the analysis.'),
        ('7e_evidence_attachment_needed', 'Attach documented evidence.'),
        ('7f_test_results_attachment_needed', 'Attach test results.'),
    ],
    'form_handler_trader': [
        ('1l_certificate_attachment_needed', 'Attach a copy of your current State certificate.'),
        ('2a_documentation_attachment_needed', 'Provide all documentation.'),
        ('2b_certificate_attachment_needed', 'Attach a copy of your current organic certificate.'),
        ('2c_certificate_attachment_needed', 'Attach a copy of your previous organic certificate.'),
        ('2d_documentation_attachment_needed', 'Attach documentation that verified non-compliances have been addressed.'),
        ('4c_nonorganic_list_attachment_needed', 'If non-organic product is handled, submit a list of the non-organic product handled at this operation.'),
        ('5b_supply_chain_attachment_needed', 'Attach the Master Supply Chain and Product List document.'),
        ('7g_evidence_attachment_needed', 'Attach documented evidence.'),
    ],
    'form_manejo_proceso': [
        ('1l_certificate_attachment_needed', 'Adjunte una copia de su certificado Estatal más actual.'),
        ('2a_documentation_attachment_needed', 'Envíe toda la documentación.'),
        ('2b_certificate_attachment_needed', 'Adjunte una copia del certificado actual.'),
        ('2c_certificate_attachment_needed', 'Adjunte una copia de su certificado orgánico anterior.'),
        ('2d_documentation_attachment_needed', 'Adjunte documentación que indique que se han verificado y resuelto los incumplimientos.'),
        ('4g_ingredients_list_attachment_needed', 'Presente una lista de los ingredientes utilizados y, para cada uno, indique si es de origen orgánico.'),
        ('5b_supply_chain_attachment_needed', 'Adjunte el documento de la Lista Maestra de la Cadena de Suministro.'),
        ('6i_results_attachment_needed', 'Adjunte los resultados de los análisis.'),
        ('7e_evidence_attachment_needed', 'Adjunte evidencia documentada.'),
        ('7f_test_results_attachment_needed', 'Adjunte resultados del análisis.'),
    ],
    'form_comercializador': [
        ('1l_certificate_attachment_needed', 'Adjunte una copia de su certificado Estatal más actual.'),
        ('2a_documentation_attachment_needed', 'Facilite toda la documentación.'),
        ('2b_certificate_attachment_needed', 'Adjunte una copia del certificado actual.'),
        ('2c_certificate_attachment_needed', 'Adjunte una copia de su certificado orgánico anterior.'),
        ('2d_documentation_attachment_needed', 'Adjunte documentación que indique que se han verificado y resuelto los incumplimientos.'),
        ('4c_nonorganic_list_attachment_needed', 'Si se manipulan productos no orgánicos, presente una lista de los productos no orgánicos manipulados en esta operación.'),
        ('5b_supply_chain_attachment_needed', 'Adjunte el documento de la Lista Maestra de la Cadena de Suministro.'),
        ('7g_evidence_attachment_needed', 'Adjunte pruebas documentadas.'),
    ],
    'form_cultivo': [
        ('1l_certificate_attachment_needed', 'Adjunte una copia de su certificado Estatal más actual.'),
        ('2a_documentation_attachment_needed', 'Envíe toda la documentación.'),
        ('2b_certificate_attachment_needed', 'Adjunte una copia del certificado actual.'),
        ('2c_certificate_attachment_needed', 'Adjunte una copia de su certificado orgánico anterior.'),
        ('2d_documentation_attachment_needed', 'Adjunte documentación que indique que se han verificado y resuelto los incumplimientos.'),
        ('5b_supply_chain_attachment_needed', 'Adjunte el documento de la Lista Maestra de la Cadena de Suministro.'),
        ('6n_test_results_attachment_needed', 'Adjunte el análisis de residuos y/o resultados de pruebas de salinidad, si aplica.'),
        ('7b_statements_attachment_needed', 'Presente declaraciones firmadas del administrador anterior indicando el uso y todos los insumos aplicados durante los 3 años previos.'),
        ('8a_seeds_attachment_needed', 'Envíe documentos de soporte para las semillas enumeradas arriba.'),
        ('9d_test_results_attachment_needed', 'Adjunte copias de los resultados de las pruebas disponibles.'),
        ('9k_documentation_attachment_needed', 'Si usa estiércol crudo y tiene cultivos para consumo humano, adjunte documentación de soporte (tipo de cultivo, área aplicada, fecha de aplicación y fecha propuesta de cosecha).'),
        ('9o_analysis_attachment_needed', 'Adjunte análisis de residuos/especificaciones de aditivos de estiércol, si están disponibles.'),
        ('15a_diagrams_attachment_needed', 'Adjunte un diagrama de flujo y un plano de planta.'),
        ('15e_evidence_attachment_needed', 'Adjunte evidencia documental.'),
        ('15r_label_attachment_needed', 'Adjunte etiqueta.'),
        ('15s_test_kit_attachment_needed', 'Si se monitorean los niveles de cloro, adjunte una etiqueta o especificación del kit de prueba utilizado.'),
        ('16e_supporting_document_attachment_needed', 'Puede adjuntar una lista de los registros que mantiene en su operación.'),
        ('16k_documents_attachment_needed', 'Envíe los documentos enumerados arriba.'),
        ('19_certification_attachment_needed', 'Adjunte una copia del certificado actual (no es necesario completar la tabla siguiente).'),
    ],
}
