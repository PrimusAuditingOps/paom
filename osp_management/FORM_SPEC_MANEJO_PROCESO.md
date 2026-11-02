# Especificación técnica — Formulario "Manejo o Proceso" (Organic System Plan)

> ✅ **ESTADO: FORMULARIO COMPLETO CONSTRUIDO** (18/ago) — las 15 secciones y las 3 tablas dinámicas (`4b_sites_json`, `5d_products_json`, `9a_inputs_json`) están implementadas en `views/osp_form_manejo_proceso.xml` + `static/src/js/osp_form.js` (`TABLE_CONFIGS.manejo_sites`/`manejo_products`/`manejo_inputs`). Reporte PDF: `report/osp_manejo_proceso_report_data.py` + `get_manejo_proceso_report_sections()` (`report/osp_manejo_proceso_report.py`). Ver `CONTEXT.md` §22 para el detalle de arquitectura, incluida la regla importante de valores internos Sí/No en inglés (`Yes`/`No`) aunque las etiquetas visibles estén en español. **Formulario nativo en español** — no es traducción de otro, aunque su estructura de 15 secciones coincide casi punto por punto con `FORM_SPEC_HANDLER.md`.

Fuente: `Manejo o proceso.docx` (PrimusAuditingOps), **15 secciones**. `technical_code` reservado: `form_manejo_proceso` (ya sembrado en `data/osp_form_template_data.xml`).

## Nota importante sobre idioma

Este formulario **se muestra siempre en español**, tal cual viene en el Word — igual que Crop/Handler/Trader se muestran siempre en inglés. Esto es coherente con la regla ya establecida: **el cuerpo de cada formulario nunca se traduce**, es un documento único en un idioma fijo. Aquí el idioma fijo simplemente es español en vez de inglés. El resto de la plataforma (menús, backend, portal) sigue en su idioma normal (inglés fijo en backend, bilingüe en portal) — no cambia nada de eso.

## Decisiones heredadas de Crop/Handler/Trader (no se vuelven a preguntar)

1. **Estado/País como selects reales** (`res.country.state`/`res.country`), aunque el Word traiga texto libre.
2. **Sección 7b (Almacén) como 4 grupos de campos fijos** (Ingredientes/Productos Terminados/Material de Empaque/Otros) — mismo patrón exacto que la 7b de Handler, ya en español en el Word (`Ingredientes`, `Productos Terminados`, `Material de Empaque`, `Otros:`).
3. **11c y 13d no traen control Sí/No en el Word** (mismo hueco que en Handler) — se agrega Sí/No + textbox condicional, igual que se decidió para Handler.
4. **Falta el campo Fecha en la Sección 15 (Afirmación)** — se agrega igual que en Handler, por consistencia.
5. **Errores tipográficos/numeración del Word se corrigen silenciosamente cuando son obvios** (ej. la Sección 12 trae una pregunta "12. ¿Qué controles de plagas...?" sin letra, entre 12b y 12d — claramente debía ser "12c", se corrige sin preguntar, mismo criterio que ya se aplicó a "Legal Patnership" en Crop).

---

## Encabezado

Seleccione una opción: Primera aplicación / Actualización → `1_applicant_type` (`"First time"` / `"Update"` — mismos VALORES internos que los demás formularios, aunque la etiqueta visible esté en español, para mantener consistencia interna del dato).

---

## Sección 1: General Information — mapea letra por letra igual que Handler

| # | Pregunta (español, tal cual el Word) | Tipo | JSON key |
|---|---|---|---|
| 1a | Nombre de la Organización | text | `1a_org_name` |
| 1b | Nombre de la finca (dba) | text | `1b_dba_name` |
| 1c | Dirección | text | `1c_address` |
| 1d | Ciudad | text | `1d_city` |
| 1e | Estado | select (res.country.state) | `1e_state` |
| 1f | Código Postal | text | `1f_zip` |
| 1g | País | select (res.country) | `1g_country` |
| 1h | Información de Facturación (igual que física + 5 campos) | checkbox + text×5 | `1h_same_as_billing`, `1h_billing_address`, `1h_billing_city`, `1h_billing_state`, `1h_billing_zip`, `1h_billing_country` |
| 1i | Representante Legal (Nombre/Correo/Teléfono) | text×3 | `1i_legal_rep_name`, `1i_legal_rep_email`, `1i_legal_rep_phone` |
| 1j | Representantes Autorizados | **table** | `1j_contacts_json` (columnas: name/email/phone) |
| 1k | Estatus Legal (dropdown) + otra especifique | select + text | `1k_legal_status` (`Propietario Individual`/`Fideicomiso o Sin Fines de Lucro`/`Corporacion`/`Cooperativa`/`Asociacion Legal (forma federal 1065)`/`Otra`), `1k_legal_status_other` |
| 1l | ¿Registro Estatal? + # + adjunto | radio_yn + text | `1l_state_registration`, `1l_state_reg_number` (+ marker `1l_certificate_attachment_needed`) |
| 1m | ¿Copia de estándares NOP? | radio_yn | `1m_nop_standards_copy` |
| 1n | Descripción de actividades | textarea | `1n_description` |
| 1o | Meses de producción | text | `1o_months_production` |
| 1p | Horarios laborales | text | `1p_business_hours` |
| 1q | Idioma de inspección | text | `1q_inspection_language` |
| 1r | Idioma de documentación | text | `1r_documentation_language` |
| 1s | ¿Su operación produce o maneja? | select | `1s_produce_or_handle` — opciones: `Orgánico y No-Orgánico` / `Solo Orgánico` (decisión confirmada, ver abajo — el Word traía por error las opciones de Crop) |
| 1t | Indicaciones de ubicación / GPS | textarea | `1t_directions` |
| 1t | Horario disponible para contactar / inspección | select×2 | `1t_available_contact` (`Mañana`/`Tarde`/`Noche`/`Cualquier tiempo`), `1t_available_inspection` (`Mañana`/`Tarde`/`Cualquier tiempo` — nota: sin "Noche" en esta segunda lista, tal cual el Word) |
| 1u | Ingreso ≤ $5,000 + reventa como orgánico (condicional) | radio_yn×2 | `1u_income_5000_or_less`, `1u_resell_as_organic` |
| 1v | ¿Renovación? + resumen de cambios (condicional) | radio_yn + textarea | `1v_is_renewal`, `1v_changes_summary` |
| 1w | Auto-auditoría + fecha (condicional) | radio_yn + date | `1w_self_audit`, `1w_self_audit_date` |

---

## Sección 2 y 3 — mismo contenido que Handler (traducido, no literal palabra por palabra pero semánticamente idéntico)

Mismas keys: `2_na`, `2a_denied_certification`, `2a_certifier_and_docs` (+ `2a_documentation_attachment_needed`), `2b_certified_elsewhere` (+ `2b_certificate_attachment_needed`), `2c_previously_certified` (+ `2c_certificate_attachment_needed`), `2d_noncompliances_na`, `2d_noncompliances_details` (+ `2d_documentation_attachment_needed`), `3_na`, `3a_market_types` (`Importación directa`/`Importación indirecta`/`Exportación directa`/`Exportación indirecta`). Sección 3 trae una nota extra sobre Canadá (informativa, sin campo): *"Si está exportando a Canadá, complete el Addenda de Equivalencia Orgánica de Canadá."*

---

## Sección 4: Información de la Instalación y Productos — igual que Handler Sección 4

| # | Pregunta | Tipo | JSON key | Opciones |
|---|---|---|---|---|
| 4a | Tipo de operación (todas las que apliquen) | checkbox_group | `4a_operation_types` (+ `_other`) | `Cuarto frío/Almacenamiento en frío`, `Almacenamiento y distribución`, `Empacadora`, `Procesadora`, `Comercializador/intermediario`, `Otros` |
| 4b | ¿Otros sitios? | radio_yn | `4b_other_sites` | |
| 4b | **Tabla de sitios** | **table** | `4b_sites_json` | columnas: `site_id`, `site_address`, `city_state`, `zip_code`, `contact`, `description` (6 columnas, igual que Handler) |
| 4c | Diagrama de flujo adjunto | radio_yn | `4c_flow_diagram_attached` | |
| 4d | Productos no-orgánicos manejados | checkbox (N/A) + textarea | `4d_nonorganic_products_na`, `4d_nonorganic_products` | |
| 4e | % producción orgánica/no-orgánica | text×2 | `4e_pct_nonorganic`, `4e_pct_organic` | |
| 4f | ¿Otras certificaciones? | radio_yn + text | `4f_other_certifications`, `4f_other_certifications_details` | |
| 4g | ¿Usa/agrega ingredientes? | radio_yn | `4g_uses_ingredients` (+ marker `4g_ingredients_list_attachment_needed`) | |
| 4h | Prevención de contaminación | checkbox (N/A) + textarea | `4h_contamination_prevention_na`, `4h_contamination_prevention` | |

---

## Sección 5: Productos — igual que Handler Sección 5 (SÍ incluye la columna "empacado con esta etiqueta")

| # | Pregunta | Tipo | JSON key | Opciones |
|---|---|---|---|---|
| 5a | Tipo de mercado | checkbox_group | `5a_marketing_types` (+ `_other`) | `Directo al Minorista`, `Venta al por Mayor`, `Venta al por menor en la finca`, `A granel para un procesador`, `Contrato con comprador`, `Mercado de Agricultores`, `CSA/Servicio de suscripción`, `Otro` |
| 5b | Lista de cadena de suministro adjunta | radio_yn | `5b_supply_chain_attached` | |
| 5c | ¿Lista de marcas en certificado? | radio_yn | `5c_list_all_id_marks` | |
| 5d | **Tabla Productos** | **table** | `5d_products_json` | columnas: `product`, `id_mark`, `label_type` (texto: `Minorista`/`Mayoreo`/`Etiqueta Privada`), `packing_with_id` (Y/N — **sí presente**, a diferencia de Trader), `organic_or_100` (texto libre), `international_market` (texto) |

---

## Sección 6: Biodiversidad y Recursos Naturales — igual que Handler Sección 6 (sin choque de letras, secuencial 6a-6m)

Mismas keys que Handler: `6a_biodiversity_program`, `6b_natural_resources`, `6_water_use_na`, `6c_water_source`, `6d_water_analysis_attached`+`6d_water_analysis_doc_name`, `6e_water_conservation`, `6f_water_use_capacity`, `6g_onsite_water_treatments`, `6_boiler_na`, `6h_steam_contact`, `6h_boiler_chemicals_used`, `6h_boiler_chemicals_attached`, `6h_contamination_prevention`, `6i_boiler_condensation_tested` (+ marker `6i_results_attachment_needed`), `6j_waste_management`, `6k_recycle_waste`+`6k_recycle_describe`, `6l_energy_conservation`, `6m_air_quality`.

---

## Sección 7: Almacenamiento y Manejo Post Cosecha — igual que Handler Sección 7

Mismas keys que Handler: `7a_storage_areas`, tabla fija `7b` (prefijo `7b_ingredients_...`/`7b_finished_goods_...`/`7b_packaging_materials_...`/`7b_other_...` + `7b_other_label`, mismas 5 columnas: id_name/type/dedicated_organic/offsite_used/capacity), `7c_shipping_form`, `7d_packaging_material_type`, `7e_packaging_free_of_synthetics` (yn_na) + `7e_explain` + marker `7e_evidence_attachment_needed`, `7f_water_used_postharvest`+`7f_direct_contact`+`7f_water_documented` (+ marker `7f_test_results_attachment_needed`), `7g_offsite_storage`.

---

## Sección 8: Equipo y Sanitización — igual que Handler Sección 8

Mismas keys: `8a_equipment_list` (textarea, NO tabla — igual que Handler), `8b_equipment_dedicated_organic`+`8b_prevention_practices`, `8c_equipment_cleaned` (yn_na), `8d_cleaning_procedures`, `8e_personnel_measures`, `8f_sanitation_program`, `8_chlorine_na`, `8g_use_chlorine`, `8h_chlorine_details`, `8i_chlorine_verification`, `8j_commodities_sampled`+`8j_tools_dedicated`+`8j_cleaning_description`.

---

## Sección 9: Insumos — tabla dinámica, dropdown DISTINTO al de Handler

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 9a | **Tabla Insumos** | **table** | `9a_inputs_json` | columnas: `input_used_for` (select: `Fertilidad`/`Control de Plagas`/`Enfermedades`/`Poscosecha`/`Tratamiento Semilla`/`Tratamiento Perenne` — **coincide con el dropdown de Crop, no con el de Handler**), `brand_name`, `ingredients`, `food_contact` (Y/N), `compliance_approval_by`, `label_docs_attached` (Y/N), `restrictions_description` |

---

## Sección 10: Transporte — igual que Handler Sección 10

Mismas keys: `10a_responsible_for_transport`, `10b_receiving_method`, `10c_shipping_method`, `10d_unsealed_or_reusable`, `10d_verification_methods` (checkbox_group + `_other`).

---

## Sección 11: Envasado — igual que Handler Sección 11 (con el mismo hueco en 11c)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| — | No aplica esta sección | checkbox | `11_na` | |
| 11a | Tipo de envase | text | `11a_packaging_type` | |
| 11b | ¿Grado alimenticio? | radio_yn | `11b_food_grade` | |
| 11c | ¿Se reutilizan? | radio_yn | `11c_reused` | **agregado** (el Word no trae el control, mismo criterio que Handler) |
| 11c | Uso previo | textarea | `11c_previous_use` | condicional a Yes |
| 11c | Procedimiento de limpieza | textarea | `11c_cleaning_procedure` | condicional a Yes |
| 11d | ¿Libre de sintéticos? + verificación | radio_yn + textarea | `11d_free_of_synthetics`, `11d_verification` | |

---

## Sección 12: Control de Plagas — igual que Handler Sección 12, con 1 opción extra y typo corregido

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 12a | Responsable del control de plagas | radio (`Interno`/`Contratado`) | `12a_pest_control_responsible` | + `12a_contractor_info` condicional |
| 12b | ¿Problemas de plagas? | radio_yn | `12b_pest_issues` | + `12b_problem_pests` condicional |
| 12c | Controles de plagas *(el Word dice solo "12." — se corrige a 12c)* | checkbox_group | `12c_pest_controls` (+ `_other`) | `Remoción de Hábitat`, `Saneamiento`, `Mecánicas (Trampas)`, `Trampas de feromonas`, **`Monitoreo`** (opción extra que Handler no tiene), `Lista nacional de materiales permitidos`, `Materiales Prohibidos`, `Otros` |
| 12d | Estrategias de prevención | textarea | `12d_prevention_strategies` | |
| 12e | ¿Prácticas documentadas? | radio_yn | `12e_practices_documented` | |
| 12f | ¿Documenta suficiencia? | radio_yn | `12f_sufficiency_documented` | |
| 12g | ¿Materiales en áreas de proceso? | radio_yn + textarea condicional | `12g_materials_in_processing_areas`, `12g_contamination_prevention` | |
| 12h | ¿Materiales no listados? + justificación | radio_yn×2 | `12h_unlisted_materials_used`, `12h_justification_documented` | |
| 12i | ¿Prácticas documentadas? + registros usados | radio_yn + checkbox_group | `12i_practices_documented_records`, `12i_records_used` (+ `_other`) | |
| 12j | Monitoreo de efectividad | textarea | `12j_monitor_effectiveness` | |
| 12k | Calificación | select | `12k_effectiveness_rating` | `Excelente`/`Satisfactorio`/`Necesita mejorar` |
| 12l | Cambios anticipados | textarea | `12l_anticipated_changes` | |

---

## Sección 13: Sistema de Mantenimiento de Registros — igual que Handler Sección 13, mismo hueco en 13d

Mismas keys que Handler: `13a_traceback_description`, `13b_lot_system`, `13c_lot_number_packaging`, `13d_claim_identification` (**agregado Sí/No**, el Word solo trae FORMTEXT) + `13d_claim_identification_details` condicional, `13e_organic_records`, `13f_records_5years`, `13g_nonorganic_records` (+ `_other`), `13h_monitoring_practices`, `13i_monitoring_frequency`, `13j_fraud_prevention_program`, `13k_fraud_prevention_docs`, `13l_fraud_prevention_monitoring`.

---

## Sección 14: Trazabilidad y Balance de Masas — sin campos

Texto informativo, estático (misma explicación que Crop/Handler/Trader, traducida).

---

## Sección 15: Afirmación

| Campo | Tipo | JSON key | Notas |
|---|---|---|---|
| Nombre del Representante Autorizado | text | `15_name` | |
| Firma del Representante Autorizado | text | `15_signature` | |
| Fecha | date | `15_date` | **agregado** (el Word no lo trae, igual que en Handler) |

---

## Marcadores de "adjunto pendiente"

| Sección | Instrucción del Word | JSON key | Condicional a |
|---|---|---|---|
| 1l | Adjunte copia del certificado Estatal | `1l_certificate_attachment_needed` | `1l_state_registration` = Yes |
| 2a | Enviar toda la documentación | `2a_documentation_attachment_needed` | `2a_denied_certification` = Yes |
| 2b | Adjuntar copia del certificado actual | `2b_certificate_attachment_needed` | `2b_certified_elsewhere` = Yes |
| 2c | Adjuntar copia del certificado anterior | `2c_certificate_attachment_needed` | `2c_previously_certified` = Yes |
| 2d | Adjuntar documentación de incumplimientos resueltos | `2d_documentation_attachment_needed` | — |
| 4g | Presentar lista de ingredientes | `4g_ingredients_list_attachment_needed` | `4g_uses_ingredients` = Yes |
| 6i | Adjuntar resultados del análisis (caldera) | `6i_results_attachment_needed` | `6i_boiler_condensation_tested` = Yes |
| 7e | Adjuntar evidencia documentada | `7e_evidence_attachment_needed` | `7e_packaging_free_of_synthetics` = Yes |
| 7f | Adjuntar resultados del análisis (agua) | `7f_test_results_attachment_needed` | `7f_water_documented` = No |

## Punto resuelto (confirmado con el usuario, 18/ago)

**Sección 1s**: la pregunta *"¿Su operación produce o maneja?"* traía por error el dropdown de Crop (Zona de Cultivo Interior/Exterior/Ambas) en vez del de Handler. **Decisión confirmada**: se usan las opciones de Handler (`Orgánico y No-Orgánico` / `Solo Orgánico`), asumiendo que el dropdown del Word quedó mal copiado. Ya incorporado en la tabla de la Sección 1 de arriba.

**Con esto la spec queda cerrada — no hay preguntas pendientes.** Ya se puede programar el formulario completo, heredando el resto de las convenciones ya confirmadas en Crop/Handler/Trader (selects reales, filas fijas para almacén, Sí/No agregado en 11c/13d, campo Fecha agregado en la Afirmación, typo de la Sección 12 corregido a 12c).
