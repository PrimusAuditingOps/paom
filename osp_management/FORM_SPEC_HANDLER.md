# Especificación técnica — Formulario "Handler" (Organic System Plan)

> ✅ **ESTADO: FORMULARIO COMPLETO CONSTRUIDO** (18/ago) — las 15 secciones y las 3 tablas dinámicas (`4b_sites_json`, `5d_products_json`, `9a_inputs_json`) están implementadas en `views/osp_form_handler.xml` + `static/src/js/osp_form.js` (`TABLE_CONFIGS.handler_sites`/`handler_products`/`handler_inputs`). La Sección 7b (Storage) se construyó como 4 grupos de campos fijos, sin componente de tabla. Reporte PDF: `report/osp_handler_report_data.py` + `get_handler_report_sections()` (`report/osp_handler_report.py`), sobre el motor genérico ya generalizado en `report/osp_report_common.py`. Ver `CONTEXT.md` §18 para el detalle de arquitectura y de la generalización del reporte PDF a multi-formulario.

Fuente: `Handler.docx` (PrimusAuditingOps), **15 secciones** (más corto que Crop, que tiene 20). `technical_code` reservado: `form_handler` (ya sembrado en `data/osp_form_template_data.xml`, ver `CONTEXT.md` §11).

## Convenciones (idénticas a Crop, ver `FORM_SPEC_CROP.md` para el detalle completo)

- **JSON key**: `<sección><letra>_<nombre_corto>`, snake_case.
- **Tipos de campo**: `text`, `textarea`, `date`, `radio_yn`, `radio_yn_na`, `select`, `checkbox`, `checkbox_group`, `table` (dinámica, agregar/quitar fila — usada en `4b_sites_json` y `9a_inputs_json`). La sección 7b (Storage) NO usa tabla — se resolvió como 4 grupos de campos fijos, sin tocar el motor genérico (ver Sección 7 y "Decisiones confirmadas").
- **Adjuntos**: mismo criterio que Crop — si el Word ya trae una pregunta Sí/No que funciona como identificador, se reutiliza; si solo trae una instrucción tipo "Attach X"/"Submit X" sin Sí/No asociado, se agrega un campo booleano `_attachment_needed`.
- **Condicionales**: se ocultan con JS mientras la pregunta padre no sea "Yes" (o la opción que dispara el campo).
- Varias secciones de Handler (1, 2, 3) tienen **texto y estructura idéntica** a las mismas secciones de Crop — se reutilizan literalmente las mismas JSON keys ya usadas ahí (no hay riesgo de colisión: cada `osp.request` pertenece a un solo `form_template_id`, `form_data` nunca mezcla dos formularios).

---

## Encabezado (antes de Sección 1)

| Pregunta | Tipo | JSON key | Opciones |
|---|---|---|---|
| Choose one: First time applicant / This is an update... | radio | `1_applicant_type` | `"First time"` / `"Update"` — igual que Crop |

---

## Sección 1: General Information (205.201, 205.401) — idéntica a Crop salvo 4 letras menos

| # | Pregunta | Tipo | JSON key | Opciones / Notas |
|---|---|---|---|---|
| 1a | Organization Name | text | `1a_org_name` | sync → `organization_name` |
| 1b | dba Name | text | `1b_dba_name` | sync → `dba_name` |
| 1c | Address | text | `1c_address` | sync → `street` |
| 1d | City | text | `1d_city` | sync → `city` |
| 1e | State | select (res.country.state) | `1e_state` | Word trae `FORMTEXT` libre, pero se construye como select cascada, igual que Crop (ver Preguntas abiertas #1) — sync → `state_id` |
| 1f | Zip code | text | `1f_zip` | sync → `zip_code` |
| 1g | Country | select (res.country) | `1g_country` | sync → `country_id` |
| 1h | Billing info: checkbox "Same as Physical" + Address/City/State/Zip/Country | checkbox + text×5 | `1h_same_as_billing`, `1h_billing_address`, `1h_billing_city`, `1h_billing_state`, `1h_billing_zip`, `1h_billing_country` | si se marca, ocultar/deshabilitar los 5 campos |
| 1i | Legal Representative: Name/Email/Phone | text×3 | `1i_legal_rep_name`, `1i_legal_rep_email`, `1i_legal_rep_phone` | |
| 1j | Authorized Contacts | **table** | `1j_contacts_json` | columnas: `name`, `email`, `phone` |
| 1k | Organization Legal status ("Choose an item") + "if other, specify" | select + text | `1k_legal_status`, `1k_legal_status_other` | opciones (extraídas del docx, mismo typo que Crop): `Sole Proprietorship`, `Trust or Non-Profit`, `Corporation`, `Cooperative`, `Legal Partnership (federal form 1065)` *(corregido de "Legal Patnership")*, `Other` |
| 1l | State registration Y/N + # si aplica | radio_yn + text | `1l_state_registration`, `1l_state_reg_number` | attachment marker: `1l_certificate_attachment_needed` (condicional a Yes) |
| 1m | Copy of current NOP organic standards | radio_yn | `1m_nop_standards_copy` | |
| 1n | Description of operation's activities | textarea | `1n_description` | |
| 1o | Months of Production | text | `1o_months_production` | |
| 1p | Business hours | text | `1p_business_hours` | |
| 1q | Inspection language preference | text | `1q_inspection_language` | |
| 1r | Documentation language | text | `1r_documentation_language` | |
| 1s | What does your operation produce or handle | select | `1s_produce_or_handle` | opciones: `Organic & Non-Organic Product`, `Organic Only` — **nota**: Handler NO tiene el equivalente al `1s_operation_type` de Crop (Indoor/Outdoor Crop Area) — no aplica a un handler, se omite a propósito |
| 1t | Driving directions / GPS confirmation | textarea | `1t_directions` | |
| 1t | When available to contact | select | `1t_available_contact` | opciones: `Morning`, `Evening`, `Afternoon` |
| 1t | When available for inspection | select | `1t_available_inspection` | opciones: `Morning`, `Evening`, `Afternoon` |
| 1u | Income ≤ $5,000/año | radio_yn | `1u_income_5000_or_less` | |
| 1u | (si sí) ¿Vende a quien revenda como "orgánico"? | radio_yn | `1u_resell_as_organic` | condicional a 1u=Yes |
| 1v | ¿Es renovación? ¿Cambió algo desde la última certificación? | radio_yn | `1v_is_renewal` | |
| 1v | Si sí, resuma los cambios | textarea | `1v_changes_summary` | condicional |
| 1w | ¿Realizó auto-auditoría orgánica? | radio_yn | `1w_self_audit` | |
| 1w | Si sí, indique fecha | date | `1w_self_audit_date` | condicional |

---

## Sección 2: Prior Organic Certification and/or Noncompliance (205.405(e)) — texto IDÉNTICO a Crop

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| — | Not applicable to my operation | checkbox | `2_na` | |
| 2a | ¿Alguna vez le negaron/suspendieron/revocaron certificación? | radio_yn | `2a_denied_certification` | |
| 2a | Si sí, nombre del certificador y toda la documentación | textarea | `2a_certifier_and_docs` | condicional; attachment marker `2a_documentation_attachment_needed` |
| 2b | ¿Certificada actualmente con otra agencia? | radio_yn | `2b_certified_elsewhere` | attachment marker `2b_certificate_attachment_needed` (condicional Yes) |
| 2c | (Solo primera vez) ¿Ha sido certificada orgánica antes? | radio_yn_na | `2c_previously_certified` | attachment marker `2c_certificate_attachment_needed` (condicional Yes) |
| 2d | No-conformidades de última certificación y cómo se atendieron | checkbox (N/A) + textarea | `2d_noncompliances_na`, `2d_noncompliances_details` | attachment marker `2d_documentation_attachment_needed` |

---

## Sección 3: International Markets (205.201, 205.273, 205.300(b)(c)) — texto IDÉNTICO a Crop

| # | Pregunta | Tipo | JSON key | Opciones |
|---|---|---|---|---|
| — | Not applicable to my operation | checkbox | `3_na` | |
| 3a | Select all that applies | checkbox_group | `3a_market_types` | `Import Directly`, `Import Indirectly`, `Export Directly`, `Export Indirectly` |
| — | *(informativo: si aplica alguna, requiere International Markets OSP Addendum)* | — | — | solo texto |

---

## Sección 4: Facility Information & Products (205.201, 205.401) — NUEVA (no existe en Crop)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 4a | Indicate the type of operation (select all that apply) | checkbox_group | `4a_operation_types` (+ `4a_operation_types_other` texto) | `Cooling/Cold Storage`, `Storage and Distribution`, `Packinghouse`, `Processing`, `Trader/Broker`, `Other` |
| 4b | ¿Maneja otros sitios además del de la Sección 1? | radio_yn | `4b_other_sites` | |
| 4b | **Tabla de sitios** (si sí) | **table** | `4b_sites_json` | columnas: `site_id`, `site_address`, `city_state`, `zip_code`, `contact`, `description` — mismo patrón que la tabla Sites de Crop (4g) |
| 4c | Operation Flow Diagram Attached | radio_yn | `4c_flow_diagram_attached` | el Yes/No ya funciona como identificador del adjunto |
| 4d | Lista de productos no-orgánicos manejados | checkbox (N/A) + textarea | `4d_nonorganic_products_na`, `4d_nonorganic_products` | |
| 4e | % proyectado de producción orgánica/no-orgánica | text×2 | `4e_pct_nonorganic`, `4e_pct_organic` | |
| 4f | ¿Tiene certificaciones además de Orgánico? | radio_yn | `4f_other_certifications` | |
| 4f | Empresa auditora y esquema(s) | text | `4f_other_certifications_details` | condicional |
| 4g | ¿Utiliza/agrega ingredientes para procesar productos? | radio_yn | `4g_uses_ingredients` | attachment marker `4g_ingredients_list_attachment_needed` (condicional Yes — "submit a list of the ingredients") |
| 4h | Cómo previene contaminación/mezcla orgánico/no-orgánico | checkbox (N/A) + textarea | `4h_contamination_prevention_na`, `4h_contamination_prevention` | |

---

## Sección 5: Products – To Be Listed on Certificate by ID Mark & Market (205.201(a), 205.300)

| # | Pregunta | Tipo | JSON key | Opciones |
|---|---|---|---|---|
| 5a | Type of Marketing — select all that apply | checkbox_group | `5a_marketing_types` (+ `5a_marketing_other` texto) | `Farmers market`, `direct to retail`, `CSA/subscription service`, `wholesale`, `on-farm retail`, `Bulk commodities to processor`, `contract to buyer`, `other` — idéntico a Crop |
| 5b | Master Supply Chain doc adjunto | radio_yn | `5b_supply_chain_attached` | |
| 5c | ¿Requiere que el certificado liste todos los ID Marks? | radio_yn | `5c_list_all_id_marks` | |
| 5d | **Tabla Products** | **table** | `5d_products_json` | columnas: `product`, `id_mark`, `label_type` (checkbox_group: `Retail`/`Non-Retail`/`Private Label`), `packing_with_id` (Y/N), `organic_or_100` (**texto libre**, no select — a diferencia de la tabla equivalente de Crop, ver Preguntas abiertas #5), `international_market` (texto) |
| — | *(informativo: Master Supply Chain, Private Label Agreement, International Market Addendum, Formulation Sheet, docs de soporte)* | — | — | solo texto, sin campos |

---

## Sección 6: Biodiversity & Natural Resources (205.200, 205.270) — distinta a la de Crop

| # | Pregunta | Tipo | JSON key |
|---|---|---|---|
| 6a | Describa su programa de biodiversidad | textarea | `6a_biodiversity_program` |
| 6b | Recursos naturales dentro/alrededor de la operación | textarea | `6b_natural_resources` |
| — | *Water Use* — Not applicable to my operation | checkbox | `6_water_use_na` |
| 6c | Fuente de agua | text | `6c_water_source` |
| 6d | ¿Análisis de agua adjunto (potabilidad, fuente no municipal)? + Nombre del documento | radio_yn + text | `6d_water_analysis_attached`, `6d_water_analysis_doc_name` |
| 6e | Prácticas de conservación de agua | textarea | `6e_water_conservation` |
| 6f | ¿En qué capacidad se usa el agua? | text | `6f_water_use_capacity` |
| 6g | ¿Tratamientos de agua in-situ? *(si sí: listar en Materials List — informativo, sin campo nuevo)* | radio_yn | `6g_onsite_water_treatments` |
| — | *Boiler Use* — Not applicable | checkbox | `6_boiler_na` |
| 6h | ¿El vapor tiene contacto directo con productos orgánicos? | radio_yn | `6h_steam_contact` |
| 6h | ¿Usa químicos de caldera? | radio_yn | `6h_boiler_chemicals_used` | condicional |
| 6h | Lista de químicos en Materials List. ¿Adjunto? | radio_yn | `6h_boiler_chemicals_attached` | condicional |
| 6h | Cómo previene contaminación por químicos de caldera | textarea | `6h_contamination_prevention` | condicional |
| 6i | ¿Se prueba la condensación de la caldera? | radio_yn | `6i_boiler_condensation_tested` | attachment marker `6i_results_attachment_needed` (condicional Yes) |
| — | *Waste Management* | — | — | (sin checkbox N/A visible) |
| 6j | Prácticas de manejo de residuos | textarea | `6j_waste_management` |
| 6k | ¿Recicla materiales de desecho? + Describa | radio_yn + textarea | `6k_recycle_waste`, `6k_recycle_describe` |
| — | *Energy Conservation & Air Quality* | — | — | |
| 6l | Prácticas de conservación de energía | textarea | `6l_energy_conservation` |
| 6m | Prácticas de calidad del aire | textarea | `6m_air_quality` |

---

## Sección 7: Maintenance of Organic Integrity – Storage & Post Harvest Handling (205.270, 205.272)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 7a | Áreas utilizadas para almacenamiento | textarea | `7a_storage_areas` | |
| 7b | **Storage — 4 grupos de campos fijos, NO es tabla/componente dinámico** | 4× (text+text+radio_yn+radio_yn+text) | `7b_ingredients_id_name`/`_type`/`_dedicated_organic`/`_offsite_used`/`_capacity`; `7b_finished_goods_...` (mismas 5); `7b_packaging_materials_...` (mismas 5); `7b_other_label` + `7b_other_...` (mismas 5) | **Decisión confirmada**: se construye como 4 grupos de campos fijos, no como tabla — cero cambios al motor JS. Filas: `Ingredients`, `Finished Goods`, `Packaging Materials`, `Other:` (con label editable). Cada grupo: `id_name` (texto), `type` (texto libre), `dedicated_organic` (Y/N — la fila Ingredients trae "No" pre-marcado en el Word original, replicar ese default), `offsite_used` (Y/N), `capacity` (texto) |
| 7c | Forma en que se envían productos terminados | text | `7c_shipping_form` | |
| 7d | Tipo de material de empaque | text | `7d_packaging_material_type` | |
| 7e | ¿Empaque libre de fungicida/preservante/fumigante sintético? | radio (`Yes`/`No`/`N/A — only for in and out operations`) | `7e_packaging_free_of_synthetics` | si No: `7e_explain` (textarea); si Yes: attachment marker `7e_evidence_attachment_needed` |
| 7f | ¿Usa agua en manejo post-cosecha? | radio_yn | `7f_water_used_postharvest` | |
| 7f | ¿Contacto directo con cultivo/superficies alimentarias? | radio_yn | `7f_direct_contact` | condicional |
| 7f | ¿Documentó cumplimiento del Safe Drinking Water Act? | radio_yn | `7f_water_documented` | condicional; attachment marker `7f_test_results_attachment_needed` (si No — "Attach test results") |
| 7g | ¿Ingredientes/productos terminados almacenados fuera de sitio? *(informativo: si sí, asegurar Master Supply Chain completo)* | radio_yn | `7g_offsite_storage` | |

---

## Sección 8: Maintenance of Organic Integrity - Equipment and Sanitation (205.270, 205.272, 205.605)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 8a | Lista de nombres de equipo usado en la operación | textarea | `8a_equipment_list` | **no es tabla** — a diferencia del Equipment de Crop (14a), aquí el Word solo pide una lista de texto libre |
| 8b | ¿Todo el equipo es dedicado orgánico? | radio_yn | `8b_equipment_dedicated_organic` | si No: `8b_prevention_practices` (textarea) |
| 8c | ¿Equipo limpiado/purgado antes de manejo orgánico? | radio (`Yes`/`No`/`N/A`) | `8c_equipment_cleaned` | |
| 8d | Procedimientos de limpieza de equipo (adjuntar procedimientos y bitácoras) | textarea | `8d_cleaning_procedures` | attachment implícito |
| 8e | Medidas para que el personal no ponga en riesgo la integridad orgánica | textarea | `8e_personnel_measures` | |
| 8f | Describa su programa de sanitización | textarea | `8f_sanitation_program` | |
| — | *Use of Chlorine* — Not applicable | checkbox | `8_chlorine_na` | |
| 8g | ¿Usa cloro o productos con cloro? | radio_yn | `8g_use_chlorine` | |
| 8h | Propósito/formulación (adjuntar etiqueta)/dónde/cómo se usa | textarea | `8h_chlorine_details` | condicional a 8g=Yes; attachment implícito |
| 8i | Cómo verifica/documenta cumplimiento NOP de cloro *(si se monitorea, adjuntar etiqueta o ficha del kit — informativo)* | textarea | `8i_chlorine_verification` | |
| — | *Quality Testing* | — | — | |
| 8j | ¿Se muestrean las materias primas orgánicas? | radio_yn | `8j_commodities_sampled` | |
| 8j | ¿Herramientas de muestreo dedicadas solo a orgánico? | radio_yn | `8j_tools_dedicated` | condicional a 8j=Yes |
| 8j | Si no, cómo se limpia el equipo de muestreo / adjuntar procedimiento | textarea | `8j_cleaning_description` | condicional a `8j_tools_dedicated`=No; attachment implícito |

---

## Sección 9: Maintenance of Organic Integrity – Inputs (205.105, 205.600) — tabla dinámica

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 9a | **Tabla Inputs** | **table** | `9a_inputs_json` | columnas: `input_used_for` (select: `Pest`/`Disease`/`Post-Harvest`/`Sanitizer`/`Other`), `brand_name`, `ingredients`, `food_contact` (Y/N — "¿Contacto directo con alimentos o superficies alimentarias?", columna **nueva** que no existe en la tabla de Inputs de Crop), `compliance_approval_by`, `label_docs_attached` (Y/N), `restrictions_description` (texto — "If Product has Restrictions") |

---

## Sección 10: Maintenance of Organic Integrity – Transportation (205.270, 205.272)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 10a | ¿Responsable del transporte de entrada/salida? | radio_yn | `10a_responsible_for_transport` | |
| 10b | ¿Cómo se reciben los productos orgánicos? | text | `10b_receiving_method` | |
| 10c | ¿Cómo se envían los productos orgánicos? | text | `10c_shipping_method` | |
| 10d | ¿Recibe en empaque permeable/sin sellar o contenedores reusables? | radio_yn | `10d_unsealed_or_reusable` | |
| 10d | Si sí, cómo verifica que no se contaminó en tránsito | checkbox_group | `10d_verification_methods` (+ `_other`) | opciones: `Notify transport companies of organic status`, `Truck inspections`, `Dedicated organic transport vehicle`, `Clean truck affidavit`, `Wash tags`, `Certified supplier provides documentation`, `Other`; condicional a 10d=Yes |

---

## Sección 11: Maintenance of Organic Integrity – Packaging (205.270, 205.272, 205.300, 205.605)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| — | Not applicable to my operation | checkbox | `11_na` | |
| 11a | ¿Qué tipo de empaque se usa? | text | `11a_packaging_type` | |
| 11b | ¿Todo el empaque es food grade? | radio_yn | `11b_food_grade` | |
| 11c | ¿Se reutilizan los materiales/contenedores de empaque? | radio_yn | `11c_reused` | agregado (el Word no traía el control Sí/No explícito, ver decisión confirmada abajo) |
| 11c | Uso previo del material | textarea | `11c_previous_use` | condicional a `11c_reused` = Yes |
| 11c | Procedimiento de limpieza antes de reutilizar | textarea | `11c_cleaning_procedure` | condicional a `11c_reused` = Yes |
| 11d | ¿Empaque libre de fungicidas/preservantes/fumigantes sintéticos? + cómo se verifica | radio_yn + textarea | `11d_free_of_synthetics`, `11d_verification` | |

---

## Sección 12: Maintenance of Organic Integrity – Pest Management (205.271)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 12a | ¿Quién es responsable del control de plagas? | radio (`In-house`/`Contracted`) | `12a_pest_control_responsible` | si Contracted: `12a_contractor_info` (texto — nombre/número + copia de factura) |
| 12b | ¿Tiene problemas de plagas? | radio_yn | `12b_pest_issues` | si sí: `12b_problem_pests` (textarea) |
| 12c | ¿Qué controles de plagas tiene? | checkbox_group | `12c_pest_controls` (+ `_other`) | `Removal of habitat`, `Sanitation`, `Mechanical (traps)`, `Pheromone traps`, `National List allowed materials`, `Prohibited materials`, `other` |
| 12d | Estrategias para prevenir daño antes de aplicar sustancia aprobada | textarea | `12d_prevention_strategies` | |
| 12e | ¿Prácticas preventivas documentadas? | radio_yn | `12e_practices_documented` | |
| 12f | ¿Documenta si las prácticas preventivas fueron suficientes antes de aplicar sustancia? | radio_yn | `12f_sufficiency_documented` | |
| 12g | ¿Materiales de control de plagas en áreas de proceso/almacén? | radio_yn | `12g_materials_in_processing_areas` | si sí: `12g_contamination_prevention` (textarea) |
| 12h | ¿Usa materiales no listados en §205.605/606? | radio_yn | `12h_unlisted_materials_used` | si sí: `12h_justification_documented` (radio_yn) |
| 12i | ¿Prácticas y uso de materiales documentados? | radio_yn | `12i_practices_documented_records` | si sí: `12i_records_used` (checkbox_group + `_other`: `Pesticide use log`, `Removal/re-entry records`, `Cleaning records`, `Other`) — *(informativo: lista de materiales ya cubierta en Sección 9)* |
| 12j | ¿Cómo monitorea la efectividad del programa de plagas? | textarea | `12j_monitor_effectiveness` | |
| 12k | Calificación de efectividad | select | `12k_effectiveness_rating` | `Excellent`, `Satisfactory`, `Needs improvement` |
| 12l | ¿Qué cambios anticipa? | textarea | `12l_anticipated_changes` | |

---

## Sección 13: Record-Keeping System (205.103, 205.400)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 13a | Cómo los registros rastrean el producto (traceback) | textarea | `13a_traceback_description` | |
| 13b | Sistema de lote/numeración | textarea | `13b_lot_system` | |
| 13c | Cómo asegura el número de lote en el empaque | textarea | `13c_lot_number_packaging` | |
| 13d | ¿Los registros identifican el reclamo aplicable (100% orgánico, etc.)? | radio_yn | `13d_claim_identification` | agregado (el Word no traía el control Sí/No explícito) |
| 13d | Explique / detalle | textarea | `13d_claim_identification_details` | condicional a `13d_claim_identification` = Yes |
| 13e | Qué registros mantiene para producción orgánica | textarea | `13e_organic_records` | *(puede enviar documento de soporte con la lista)* |
| 13f | ¿Registros mantenidos 5+ años? | radio_yn | `13f_records_5years` | |
| 13g | Qué registros mantiene para producción no-orgánica | checkbox_group | `13g_nonorganic_records` (+ `_other`) | `Not applicable, organic only`, `Same as the records listed in 13e`, `Other` |
| 13h | Prácticas/procedimientos de monitoreo | textarea | `13h_monitoring_practices` | |
| 13i | Cómo/con qué frecuencia se implementan | textarea | `13i_monitoring_frequency` | |
| 13j | Programa de prevención de fraude orgánico | textarea | `13j_fraud_prevention_program` | |
| 13k | Documentos mantenidos para prevención de fraude (y enviarlos) | textarea | `13k_fraud_prevention_docs` | attachment implícito |
| 13l | Monitoreo de efectividad del programa anti-fraude | textarea | `13l_fraud_prevention_monitoring` | |

---

## Sección 14: Trace back and Mass Balance — sin campos

Solo texto explicativo/informativo (qué es un traceback, qué es un mass balance, referencias NOP Guidance 2602). **No requiere ningún input** — igual que la Sección 17 de Crop. Se renderiza como texto estático.

---

## Sección 15: Affirmation (Firma)

Texto legal fijo (afirmaciones de cumplimiento NOP, inspecciones sin previo aviso, auditorías de cadena de suministro, Master Supply Chain and Product List) + campos:

| Campo | Tipo | JSON key | Notas |
|---|---|---|---|
| Name of Person completing this OSP | text | `15_name` | |
| Signature of Authorized Person | text (firma electrónica) | `15_signature` | |
| Date | date | `15_date` | **Decisión confirmada**: se agrega aunque no exista en el Word fuente, igual que en Crop, por consistencia y trazabilidad |

---

## Marcadores de "adjunto pendiente" (mismo criterio que Crop)

| Sección | Instrucción del Word | JSON key nuevo | Condicional a |
|---|---|---|---|
| 1l | Attach a copy of your current State certificate | `1l_certificate_attachment_needed` | `1l_state_registration` = Yes |
| 2a | Provide all documentation (certificador que negó/suspendió) | `2a_documentation_attachment_needed` | `2a_denied_certification` = Yes |
| 2b | Attach a copy of your current organic certificate | `2b_certificate_attachment_needed` | `2b_certified_elsewhere` = Yes |
| 2c | Attach a copy of your previous organic certificate | `2c_certificate_attachment_needed` | `2c_previously_certified` = Yes |
| 2d | Attach documentation que verificó no-conformidades atendidas | `2d_documentation_attachment_needed` | — |
| 4g | Submit a list of the ingredients used | `4g_ingredients_list_attachment_needed` | `4g_uses_ingredients` = Yes |
| 6i | Attach the results from the boiler condensation analysis | `6i_results_attachment_needed` | `6i_boiler_condensation_tested` = Yes |
| 7e | Attach documented evidence (empaque libre de sintéticos) | `7e_evidence_attachment_needed` | `7e_packaging_free_of_synthetics` = Yes |
| 7f | Attach test results (Safe Drinking Water Act) | `7f_test_results_attachment_needed` | `7f_water_documented` = No |

*Nota: a diferencia de Crop, aquí hay menos marcadores nuevos porque más preguntas de Handler ya traen su propio Sí/No que funciona como identificador (ej. 4c, 4f, 5b, 6d, 6h, 8g, 8j, 12g, 12h).*

## Decisiones confirmadas con el usuario (18/ago) — spec cerrada, lista para programar

1. **State/Country como selects reales** (`1e_state`/`1g_country`) — confirmado: igual que Crop, contra `res.country.state`/`res.country` con filtro en cascada, aunque el Word traiga texto libre.
2. **`7b` (Storage) se construye como 4 grupos de campos fijos**, no como componente de tabla — confirmado, cero cambios al motor JS genérico. Ver detalle de keys en la Sección 7 de arriba.
3. **11c y 13d SÍ llevan control Sí/No**, agregado explícitamente aunque el Word no lo traía — confirmado, y además cada uno lleva su textbox de texto libre condicional para capturar la explicación cuando la respuesta es "Yes" (ver keys `11c_reused`+`11c_previous_use`+`11c_cleaning_procedure`, y `13d_claim_identification`+`13d_claim_identification_details` en las secciones correspondientes arriba).
4. **Se agrega el campo Date en la Sección 15 (Affirmation)** (`15_date`) — confirmado, por consistencia con Crop y trazabilidad, aunque el Word no lo pida explícitamente.
5. **`5d_products_json`, columna "Organic or 100% Organic?"** — se construye como texto libre (texto extraído del Word), tal como está.

**Con esto la spec queda cerrada — no hay preguntas pendientes.** Ya se puede programar el formulario completo siguiendo exactamente el mismo patrón de Crop: `views/osp_form_handler.xml` (body + wrappers portal/público), rama en `controllers/portal.py`, entrada en `PUBLIC_FORM_SLUGS`, y el trío de reporte PDF (`report/osp_handler_report_data.py` + método `get_handler_report_sections()` + generalización del botón "Descargar OSP"/link "PDF" para que enrute según `technical_code`).
