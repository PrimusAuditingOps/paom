# Especificación técnica — Formulario "Crop" (Organic System Plan)

> ✅ **ESTADO: FORMULARIO COMPLETO CONSTRUIDO** (17/ago). Las 20 secciones y las 12 tablas dinámicas (1j, 4g, 4h, 4j, 5d, 8a, 8g, 10, 12a, 14a, 19, 20) están implementadas en `osp_form_crop.xml` + `osp_form.js`. Todos los `⏳ Pendiente` de este documento quedaron construidos; se conserva como referencia de las decisiones de diseño (JSON keys, opciones de selects, condicionales) por si se necesita auditar o replicar el patrón en el próximo formulario (ej. "Handler"). Ver `CONTEXT.md` para el detalle de arquitectura (motor de tablas genérico, motor de condicionales, modo admin/solo-lectura).
>
> ➕ **Sección 21 "Attachments" agregada (17/ago, no es parte del PDF original)**: sección de subida general de archivos (no ligada a un `_attachment_needed` puntual), visible solo con controles de subir/borrar mientras `state == 'draft'` y el usuario es el cliente dueño. Ver `CONTEXT.md`, punto 9.

Fuente: `Crop.pdf` (PrimusAuditingOps, Org-007 Rev.9, 1/9/2024, 21 páginas, 20 secciones).
Este documento traduce cada pregunta del PDF a una especificación de campo lista para implementar en `osp_form_crop.xml` + `osp_form.js`, siguiendo las convenciones ya usadas en las Secciones 1 (parcial) y 4 (parcial).

## Convenciones

- **JSON key**: `<sección><letra>_<nombre_corto>` en snake_case, ej. `1a_org_name`, `6h_water_source`. Coincide con el `name` del input HTML.
- **Tipos de campo**:
  - `text` — input de una línea
  - `textarea` — texto largo
  - `date` — selector de fecha
  - `radio_yn` — Sí/No
  - `radio_yn_na` — Sí/No/N/A
  - `select` — dropdown de una sola opción
  - `checkbox` — booleano único
  - `checkbox_group` — "selecciona todas las que apliquen"
  - `table` — tabla dinámica (agregar/quitar fila) — usa el patrón `SITE_FIELDS` ya construido en Sección 4g
- **Adjuntos**: el PDF pide repetidamente "attach a copy de X". **Se difiere el manejo real de subida de archivos para todas las secciones** (no está en alcance todavía), **pero sí se deja un campo identificador/marcador** de que ahí se espera un archivo — para no perder ese requisito de vista. Convención: donde el PDF ya trae una pregunta explícita "¿está adjunto? Sí/No" (ej. 4b, 4d, 4e, 5b, 7a), esa misma pregunta **ya cumple** la función de identificador — no se agrega nada extra. Donde el PDF solo trae una instrucción tipo "*Attach X*" sin pregunta Sí/No asociada, se agrega un campo booleano nuevo con sufijo `_attachment_needed` (ver tabla consolidada más abajo).
- **Campos condicionales** (dependen de una respuesta "Yes" previa, ej. 1v→1w, 2a, 4a→4b-4f, 11c, 13j, 15f→15g→15h, 19, etc.): **se ocultan con JS** mientras la pregunta padre no sea "Yes". Esta es una convención global, ya no se anota pregunta por pregunta.
- **Estado**: ✅ Construida | ⏳ Pendiente | ❓ Necesita definición (ver "Preguntas abiertas" al final)
- **Sync**: si el campo debe copiarse a un campo del modelo `osp.request` al hacer Submit (como hicimos con la Sección 1), se indica explícitamente. Todo lo demás vive únicamente en `form_data` (JSON).

---

## Sección 1: General Information — ✅ parcialmente construida (1a–1g)

| # | Pregunta | Tipo | JSON key | Opciones / Notas |
|---|---|---|---|---|
| — | Choose one: First time / Update | radio | `1_applicant_type` | valores `"First time"` / `"Update"` — ✅ construido |
| 1a | Organization Name | text | `1a_org_name` | ✅ construido, **sync → `organization_name`** |
| 1b | dba Name | text | `1b_dba_name` | ✅ construido, **sync → `dba_name`** |
| 1c | Address | text | `1c_address` | ✅ construido, sin sync (falta campo `street` en el modelo) |
| 1d | City | text | `1d_city` | ✅ construido, **sync → `city`** |
| 1e | State | select (res.country.state) | `1e_state` | ✅ construido, **sync → `state_id`**, filtrado en cascada por país |
| 1f | Zip code | text | `1f_zip` | ✅ construido, **sync → `zip_code`** |
| 1g | Country | select (res.country) | `1g_country` | ✅ construido, **sync → `country_id`** |
| 1h | Billing information (checkbox "Same as Physical" + Address/City/State/Zip/Country) | checkbox + text×5 | `1h_same_as_billing`, `1h_billing_address`, `1h_billing_city`, `1h_billing_state`, `1h_billing_zip`, `1h_billing_country` | ⏳ Si se marca "same as physical", ocultar/deshabilitar los 5 campos vía JS |
| 1i | Legal Representative: Name/Email/Phone | text×3 | `1i_legal_rep_name`, `1i_legal_rep_email`, `1i_legal_rep_phone` | ⏳ |
| 1j | Authorized Contacts (repetible) | **table** | `1j_contacts_json` | columnas: `name`, `email`, `phone` — ⏳ |
| 1k | Organization Legal status ("Choose an item") + "if other, specify" | select + text | `1k_legal_status`, `1k_legal_status_other` | ✅ opciones (extraídas del Word): `Sole Proprietorship`, `Trust or Non-Profit`, `Corporation`, `Cooperative`, `Legal Partnership (federal form 1065)`, `Other` |
| 1l | State registration Y/N + # si aplica | radio_yn + text | `1l_state_registration`, `1l_state_reg_number` | ⏳ (adjunto diferido) |
| 1m | Copy of current NOP organic standards | radio_yn | `1m_nop_standards_copy` | ⏳ |
| 1n | Description of operation's activities | textarea | `1n_description` | ⏳ |
| 1o | Months of Production | text | `1o_months_production` | ✅ confirmado: texto libre |
| 1p | Business hours | text | `1p_business_hours` | ⏳ |
| 1q | Inspection language preference | text/select | `1q_inspection_language` | ⏳ |
| 1r | Documentation language | text/select | `1r_documentation_language` | ⏳ |
| 1s | Type of operation ("Choose an item") | select | `1s_operation_type` | ✅ opciones: `Indoor Crop Area`, `Outdoor Crop Area`, `Both Indoor and Outdoor Crop Areas` |
| 1t | Does operation produce or handle ("Choose an item") | select | `1t_produce_or_handle` | ✅ opciones: `Organic & Non-Organic Product`, `Organic Only` |
| 1u | Driving directions / GPS confirmation | textarea | `1u_directions` | ⏳ |
| 1u | When available to contact ("Choose an item") | select | `1u_available_contact` | ✅ opciones: `Morning`, `Evening`, `Afternoon` |
| 1u | When available for inspection ("Choose an item") | select | `1u_available_inspection` | ✅ opciones: `Morning`, `Evening`, `Afternoon` |
| 1v | Income ≤ $5,000/año | radio_yn | `1v_income_5000_or_less` | ⏳ |
| 1v | (si sí) ¿Vende a quien revenda como "orgánico"? | radio_yn | `1v_resell_as_organic` | condicional a 1v=Yes |
| 1w | ¿Es renovación? ¿Cambió algo desde la última certificación? | radio_yn | `1w_is_renewal` | ⏳ nota roja: si hay campos nuevos, requiere Field History Affidavit (Sección 19) — solo informativo |
| 1w | Si sí, resuma los cambios | textarea | `1w_changes_summary` | condicional a 1w=Yes |
| 1x | ¿Realizó auto-auditoría orgánica? | radio_yn | `1x_self_audit` | ⏳ |
| 1x | Si sí, indique fecha | date | `1x_self_audit_date` | condicional a 1x=Yes |

---

## Sección 2: Prior Organic Certification and/or Noncompliance — ⏳

*(Solo aplica a nuevos aplicantes; renovantes pueden saltarla)*

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| — | Not applicable to my operation | checkbox | `2_na` | |
| 2a | ¿Alguna vez le negaron/suspendieron/revocaron certificación? | radio_yn | `2a_denied_certification` | si sí: nombre del certificador + docs | 
| 2a | Nombre del certificador (si aplica) | text | `2a_denied_certifier_name` | condicional |
| 2b | ¿Certificada actualmente con otra agencia? | radio_yn | `2b_certified_elsewhere` | adjunto diferido |
| 2c | (Solo primera vez) ¿Ha sido certificada orgánica antes? | radio_yn_na | `2c_previously_certified` | adjunto diferido |
| 2d | Lista de no-conformidades de última certificación y cómo se atendieron | checkbox (N/A) + textarea | `2d_noncompliances_na`, `2d_noncompliances_details` | adjunto diferido |

---

## Sección 3: International Markets — ⏳

| # | Pregunta | Tipo | JSON key | Opciones |
|---|---|---|---|---|
| — | Not applicable to my operation | checkbox | `3_na` | |
| 3a | Select all that applies | checkbox_group | `3a_market_types` | `Import Directly`, `Import Indirectly`, `Export Directly`, `Export Indirectly` |
| — | *(informativo: si aplica alguna, requiere International Markets OSP Addendum)* | — | — | solo texto, sin campo |

---

## Sección 4: Crops & Fields — ✅ parcialmente construida (solo 4g)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 4a | ¿Sitios parte de un Producer Group? | radio_yn | `4a_producer_group` | ⏳ si sí, habilita 4b–4f |
| 4b | Lista de growers adjunta | radio_yn | `4b_growers_list_attached` | ⏳ adjunto diferido |
| 4c | ¿Sitios certificados por otra agencia? | radio_yn | `4c_other_agency_certified` | ⏳ |
| 4c | Nombre de agencia previa (si aplica) | text | `4c_previous_agency_name` | condicional |
| 4d | ¿No-conformidades menores abiertas? | radio_yn | `4d_noncompliances_open` | ⏳ |
| 4d | Info adjunta (si aplica) | radio_yn | `4d_info_attached` | adjunto diferido |
| 4e | Lista de no-conformidades ICS adjunta | radio_yn | `4e_ics_list_attached` | ⏳ adjunto diferido |
| 4f | Lista de productos no-orgánicos y dónde se cultivan | textarea | `4f_nonorganic_products` | ⏳ |
| 4g | **Tabla Sites** | **table** | `4g_sites_json` | ✅ **CONSTRUIDA** — columnas: `site_id`, `site_address`, `city_state`, `zip`, `contact`, `description` |
| 4h | **Tabla Fields** | **table** | `4h_fields_json` | ⏳ columnas: `field_id`, `parcel_address`, `area_type` (select: `Organic`/`Transitional`/`Non-Organic`), `units` (Acre/Hectare), `rented_or_owned` (select: `Rented`/`Owned`) |
| 4i | ¿Mismos Field IDs en su sistema de registros? | radio_yn | `4i_same_field_ids` | ⏳ |
| 4i | Si no, explique | textarea | `4i_explain` | condicional |
| 4j | **Tabla Crops** | **table** | `4j_crops_json` | ⏳ columnas: `crop_requested`, `field_id`, `total_planted_area`, `area_units` (Acre/Hectare), `projected_yield`, `yield_units` (Acre/Hectare) |

---

## Sección 5: Products — ⏳

| # | Pregunta | Tipo | JSON key | Opciones |
|---|---|---|---|---|
| 5a | Type of Marketing | checkbox_group | `5a_marketing_types` | `Farmers market`, `direct to retail`, `CSA/subscription service`, `wholesale`, `on-farm retail`, `Bulk commodities to processor`, `contract to buyer`, `other` (+ `5a_marketing_other` texto) |
| 5b | Master Supply Chain doc adjunto | radio_yn | `5b_supply_chain_attached` | adjunto diferido |
| 5c | ¿Requiere que el certificado liste todos los ID Marks? | radio_yn | `5c_list_all_id_marks` | |
| 5d | **Tabla Products** | **table** | `5d_products_json` | columnas: `product`, `id_mark`, `label_type` (checkbox_group: Retail/Non-Retail/Private Label), `packing_with_id` (Y/N), `organic_or_100` (select), `international_market` (text) |

---

## Sección 6: Biodiversity & Natural Resources — ⏳

*(sin checkbox de "sección no aplica"; algunas preguntas individuales sí tienen N/A)*

| # | Pregunta | Tipo | JSON key |
|---|---|---|---|
| 6a | Prácticas de conservación de suelo | textarea | `6a_soil_conservation` |
| 6b | Problemas de erosión (por qué y en qué campos) | textarea | `6b_erosion_problems` |
| 6c | Esfuerzos para minimizar erosión + monitoreo | textarea | `6c_erosion_mitigation` |
| 6d | Recursos naturales dentro/alrededor de la operación | textarea | `6d_natural_resources` |
| 6e | ¿Áreas boscosas? (N/A + descripción) | checkbox + textarea | `6e_woodland_na`, `6e_woodland_details` |
| 6f | ¿Humedales? (N/A + descripción) | checkbox + textarea | `6f_wetlands_na`, `6f_wetlands_details` |
| 6g | ¿Vida silvestre/biodiversidad? (N/A + descripción) | checkbox + textarea | `6g_wildlife_na`, `6g_wildlife_details` |
| 6h | Fuente de agua | text | `6h_water_source` |
| 6i | Uso del agua | text | `6i_water_use` |
| 6j | Tipo de sistema de irrigación | text | `6j_irrigation_type` |
| 6k | Proceso de limpieza del sistema de agua | textarea | `6k_water_cleaning` |
| 6l | ¿Sistema compartido con otro operador? + qué productos usan | radio_yn + text | `6l_shared_system`, `6l_shared_products` |
| 6m | Prácticas para proteger calidad del agua | textarea | `6m_water_quality_practices` |
| 6n | Programa de pruebas de agua | textarea | `6n_water_testing` *(adjunto diferido)* |

---

## Sección 7: Land requirements — ⏳

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 7a | Field History + Updated Map adjuntos | radio_yn ×2 | `7a_field_history_attached`, `7a_updated_map_attached` | adjunto diferido |
| 7b | ¿Manejó todos los campos 3+ años? | radio_yn | `7b_managed_3years` | si no: requiere declaraciones firmadas (adjunto diferido) |
| 7c | Evidencia de no uso de sustancias prohibidas (3 años previos) | textarea | `7c_evidence_no_prohibited` | |
| 7d | ¿Límites de campos distinguibles y reflejados en mapas? | radio_yn | `7d_boundaries_defined` | |
| 7e | ¿Superficie total consistente entre mapas/historiales/OSP? | radio_yn | `7e_acreage_consistent` | |
| 7f | ¿Zonas de amortiguamiento establecidas? | select (`Yes`/`No`/`No, but not needed`) | `7f_buffer_zones` | |
| 7f | Explique / describa las zonas | textarea | `7f_buffer_zones_explain` | |

---

## Sección 8: Seeds & Planting Stock — ⏳ (2 tablas dinámicas)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| — | Not applicable to my operation (semillas) | checkbox | `8a_na` | |
| 8a | **Tabla Seeds** | **table** | `8a_seeds_json` | columnas: `crop_variety`, `brand_supplier`, `seed_type` (select: `Certified Organic`/`Non-Organic: Untreated`/`Non-Organic: Treated`/`Certified Organic Planting Stock`/`Non-Organic: Untreated Planting Stock`/`Non-Organic: Treated Planting Stock`), `non_organic_treatment` (texto, condicional), `non_gmo_documented` (Y/N), `seed_search_form_completed` (Y/N) |
| 8b | ¿Cultiva plántulas orgánicas en finca? | radio_yn_na | `8b_organic_seedlings` | |
| 8c | Pasos/procedimientos (si cultiva plántulas) | textarea | `8c_seedling_procedures` | condicional a 8b |
| 8d | Equipo del sistema de riego | textarea | `8d_watering_equipment` | |
| 8e | Prevención de enfermedades/plagas en plántulas | textarea | `8e_disease_prevention` | |
| 8f | ¿Servicios adicionales de plántulas/planting stock? | radio_yn_na | `8f_additional_services` | |
| 8f | Descripción (si sí) | textarea | `8f_additional_services_describe` | condicional |
| — | Not applicable to my operation (planting stock perenne) | checkbox | `8g_na` | |
| 8g | **Tabla Planting Stock (perennes)** | **table** | `8g_planting_stock_json` | columnas: `type_crop_variety`, `source_supplier`, `seedling_type` (select: `Certified Organic`/`Non-Organic`), `date_planted` (condicional), `expected_harvest_date` (condicional), `search_form_attached` (Y/N, condicional) |

---

## Sección 9: Soil and Crop Fertility Management — ⏳

| # | Pregunta | Tipo | JSON key |
|---|---|---|---|
| — | Not applicable (General Information/Evaluation) | checkbox | `9_general_na` |
| 9a | Tipos generales de suelo | textarea | `9a_soil_types` |
| 9b | Limitaciones químicas/físicas/biológicas | textarea | `9b_soil_limitations` |
| 9c | Prácticas para mejorar/mantener fertilidad | textarea | `9c_fertility_practices` |
| 9d | Monitoreo de efectividad *(adjunto diferido)* | textarea | `9d_monitor_effectiveness` |
| 9e | Calificación de efectividad | select (`Excellent`/`Satisfactory`/`Needs improvement`) | `9e_effectiveness_rating` |
| 9e | Cambios anticipados | textarea | `9e_anticipated_changes` |
| — | Not applicable (On-Farm Composting) | checkbox | `9_composting_na` |
| 9f | Ingredientes/aditivos de compost y proporción | textarea | `9f_compost_ingredients` |
| 9g | Método de composta | textarea | `9g_composting_method` |
| 9h | Ratio C:N inicial | text | `9h_cn_ratio` |
| 9i | ¿Temp. mantenida 131-170°F por 15+ días consecutivos? | radio_yn | `9i_compost_temp_maintained` |
| — | Not applicable (Manure Use) | checkbox | `9_manure_na` |
| 9j | Formas de estiércol usadas | checkbox_group (`Liquid`/`Semi-solid`/`Piled`/`Fully composted`/`Other`) | `9j_manure_forms` (+ `9j_manure_forms_other`) |
| 9k | Tipos de cultivos (checkbox_group) | checkbox_group | `9k_crop_types` *(adjunto diferido si usa estiércol crudo)* |
| 9l | Fuente del estiércol | radio (`on-farm`/`off-farm`) | `9l_manure_source` |
| 9m | Fuentes de estiércol externo | textarea | `9m_offfarm_manure_sources` |
| 9n | Ingredientes/aditivos del estiércol | textarea | `9n_manure_ingredients` |
| 9o | Contaminantes potenciales | textarea | `9o_manure_contaminants` |

---

## Sección 10: Crop Rotation — ⏳ (tabla dinámica)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 10 | **Tabla Crop Rotation Plans** | **table** | `10_rotation_json` | columnas: `rotation_plan` (texto), `objectives` (checkbox_group: `Increase Organic Matter`/`Nutrient Management`/`Pest or Disease Management`/`Erosion Control`/`Other`) |

---

## Sección 11: Crop pest, weed and disease management — ⏳

| # | Pregunta | Tipo | JSON key |
|---|---|---|---|
| 11a | Problemas de malezas/enfermedades y métodos de control | textarea | `11a_weed_disease_problems` |
| 11b | Tipo de estrategia restringida usada | textarea | `11b_restricted_strategy` |
| 11c | ¿Mulch removido al final de temporada? | radio_yn_na | `11c_mulch_removed` |
| 11c | Si no, por qué | textarea | `11c_mulch_not_removed_reason` |
| 11d | Problemas de plagas/enfermedades y estrategias preventivas | textarea | `11d_pest_problems` |
| 11e | ¿Prácticas preventivas documentadas? | radio_yn | `11e_practices_documented` |
| 11f | ¿Documenta insuficiencia antes de aplicar sustancia aprobada? | radio_yn | `11f_insufficiency_documented` |
| 11f | Describa brevemente | textarea | `11f_describe` |
| 11g | Monitoreo de efectividad | textarea | `11g_monitor_effectiveness` |
| 11h | Calificación de efectividad | select (`Excellent`/`Satisfactory`/`Needs improvement`) | `11h_effectiveness_rating` |
| 11i | Cambios anticipados | textarea | `11i_anticipated_changes` |

---

## Sección 12: Maintenance of Organic Integrity – Inputs — ⏳ (tabla dinámica)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 12a | **Tabla Inputs** | **table** | `12a_inputs_json` | columnas: `input_used_for` (select: `Fertility`/`Pest`/`Disease`/`Post-Harvest`/`Seed Treatment`/`Perennial Treatment`), `brand_name`, `ingredients`, `compliance_approval_by`, `label_compliance_docs_attached` (Y/N), `restrictions_compliance_description` |
| 12b | Descripción de área de almacenamiento de inputs | checkbox (N/A) + textarea | `12b_storage_na`, `12b_storage_description` | |
| 12c | Prácticas/barreras para prevenir mezcla/contaminación | textarea | `12c_prevention_practices` | |

---

## Sección 13: Buffer Areas & Split Production — ⏳

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| — | Not applicable (Buffer Areas) | checkbox | `13_buffer_na` | |
| 13a | Frecuencia de evaluación de riesgo y riesgos actuales | textarea | `13a_risk_assessment` | |
| 13b | Descripción de zonas de amortiguamiento | textarea | `13b_buffer_description` | |
| 13c | ¿Validó que son suficientes? | radio_yn | `13c_buffer_validated` | |
| 13d | Por qué son suficientes | textarea | `13d_buffer_sufficient_explain` | |
| 13e | ¿Uso de tierra colindante y zonas mostradas/actualizadas en mapas? | radio_yn | `13e_maps_updated` | |
| 13f | Uso del cultivo cosechado de zonas de buffer | textarea | `13f_buffer_harvest_use` | |
| 13g | Salvaguardas durante cosecha en zonas buffer | textarea | `13g_buffer_harvest_safeguards` | |
| 13h | Salvaguardas adicionales (checkbox_group) | checkbox_group | `13h_safeguards` (+ `13h_safeguards_other`) | opciones: `highway departments`, `electric companies`, `aerial spray companies/airports`, `adjoining landowners`, `drainage commissions`, `farm service office`, `none`, `other` |
| 13i | ¿Señales "No Spray" en caminos adyacentes? | radio_yn | `13i_no_spray_signs` | |
| 13j | ¿Campos se inundan frecuentemente? (+5 años) | radio_yn | `13j_fields_flood` | |
| 13j | Lista de números de campo (si sí) | text | `13j_flood_field_numbers` | condicional |
| — | Not applicable (Split Production) | checkbox | `13_split_na` | |
| 13k | Prácticas/barreras para prevenir contaminación (no-orgánico) | textarea | `13k_contamination_prevention` | |
| 13l | ¿Cultiva misma variedad orgánica/transición/no-orgánica? | radio_yn | `13l_same_variety_mixed` | |
| 13l | Prácticas para prevenir mezcla (si sí) | textarea | `13l_commingling_prevention` | condicional |

---

## Sección 14: Equipment & Harvest — ⏳ (tabla dinámica en 14a)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| — | Not applicable (Equipment) | checkbox | `14_equipment_na` | |
| 14a | **Tabla Equipment** | **table** | `14a_equipment_json` | columnas: `equipment_name_model_code`, `owned_rented_custom` (select: `Owned`/`Rented`/`Custom`), `used_for` (select: `Organic`/`Non-Organic`/`Both Organic and Non-Organic`), `cleaning_method` (texto) |
| — | Not applicable (Harvest) | checkbox | `14_harvest_na` | |
| 14b | ¿Cosecha mecánica o manual? + descripción | checkbox_group + textarea | `14b_harvest_method`, `14b_harvest_description` | |
| 14c | ¿Subcontrata labor de cosecha? | radio_yn | `14c_subcontract_harvest` | |
| 14c | Nombre/dirección del subcontratista | text | `14c_subcontractor_info` | condicional |
| 14d | Cómo se entrena al personal subcontratado | textarea | `14d_subcontractor_training` | |
| 14e | Contenedores usados para cosecha | text | `14e_containers_used` | |
| 14f | ¿Contenedores nuevos o usados? | radio (`New`/`Used`) | `14f_containers_condition` | |
| 14f | Qué contenían antes (si usados) | text | `14f_previous_contents` | condicional |
| 14g | ¿Contenedores exclusivos para cultivos orgánicos? | radio_yn | `14g_containers_organic_only` | |
| 14h | Problemas potenciales de contaminación/mezcla | textarea | `14h_contamination_problems` | |
| 14i | Pasos para proteger de mezcla/contaminación | textarea | `14i_protection_steps` | |

---

## Sección 15: Post-Harvest Handling, Storage and Transportation — ⏳

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| — | Not applicable (Post-Harvest Handling) | checkbox | `15_handling_na` | |
| 15a | Procedimientos/equipo de manejo post-cosecha | textarea | `15a_handling_procedures` | adjunto diferido |
| 15b | ¿Área/equipo compartido orgánico y no-orgánico? | radio_yn | `15b_shared_handling` | |
| 15b | Pasos para prevenir mezcla (si sí) | textarea | `15b_prevention_steps` | condicional |
| 15c | Forma en que se envían productos terminados | text | `15c_shipping_form` | |
| 15d | Tipos de material de empaque | text | `15d_packaging_materials` | |
| 15e | Documentación de empaque libre de fungicida/preservante sintético | textarea | `15e_packaging_documentation` | adjunto diferido |
| 15f | ¿Usa agua en manejo post-cosecha? | radio_yn_na | `15f_water_used` | |
| 15g | ¿Contacto directo con cultivo/superficies alimentarias? | radio_yn | `15g_water_direct_contact` | condicional a 15f |
| 15h | ¿Documentó que cumple Safe Drinking Water Act? | radio_yn | `15h_water_documented` | condicional |
| — | Not applicable (Storage) | checkbox | `15_storage_na` | |
| 15i | Storage Identification / Type of Crop / Type of Storage / Capacity / Used for | text×4 + select | `15i_storage_id`, `15i_storage_crop_type`, `15i_storage_type`, `15i_storage_capacity`, `15i_storage_used_for` | select `15i_storage_used_for` con opciones: `Organic`, `Transitional`, `Buffer`, `Non-Organic`, `Shared` |
| 15j | ¿Mismas áreas de storage para orgánico/transición/no-orgánico? | radio_yn | `15j_shared_storage` | |
| 15j | Cómo segrega (si sí) | textarea | `15j_segregation_method` | condicional |
| 15k | Limpieza de unidades de almacenamiento | textarea | `15k_storage_cleaning` | |
| 15l | Prevención/control de plagas en almacenamiento | textarea | `15l_pest_control_storage` | |
| 15m | ¿Ingredientes/productos almacenados fuera de sitio? | radio_yn | `15m_offsite_storage` | |
| — | Not applicable (Transportation) | checkbox | `15_transport_na` | |
| 15n | Responsable del transporte | radio (`Self`/`Buyer`/`Other`) | `15n_transport_responsible` (+ `_other`) | |
| 15o | Cómo se transportan los productos | textarea | `15o_transport_method` | |
| 15p | Problemas de contaminación/mezcla en transporte | textarea | `15p_transport_contamination_problems` | |
| 15q | Pasos para proteger integridad en transporte | checkbox_group | `15q_transport_protection_steps` (+ `_other`) | opciones: `Dedicated organic only`, `Inspecting transport units prior to loading`, `Cleaning transport units prior to loading`, `Use of Clean Truck Affidavits`, `Letter/contract with Transport Company`, `Other` |
| — | Not applicable (Use of Chlorine) | checkbox | `15_chlorine_na` | |
| 15r | ¿Usa cloro o productos con cloro? | radio_yn | `15r_use_chlorine` | |
| 15r | Propósito/formulación/dónde/cómo (si sí) | textarea | `15r_chlorine_details` | condicional, adjunto diferido |
| 15s | Verificación/documentación de cumplimiento de cloro | textarea | `15s_chlorine_verification` | adjunto diferido |

---

## Sección 16: Record Keeping System — ⏳

| # | Pregunta | Tipo | JSON key |
|---|---|---|---|
| 16a | Descripción de traceback/supply chain | textarea | `16a_traceback_description` |
| 16b | Sistema de lote/numeración | textarea | `16b_lot_system` |
| 16c | Cómo asegura número de lote en empaque | textarea | `16c_lot_number_packaging` |
| 16d | ¿Registros identifican reclamo aplicable (100% orgánico, etc.)? | radio_yn | `16d_claim_identification` |
| 16e | Qué registros mantiene para producción orgánica | textarea | `16e_organic_records` *(adjunto diferido)* |
| 16f | ¿Registros mantenidos 5+ años? | radio_yn | `16f_records_5years` |
| 16g | Qué registros mantiene para producción no-orgánica | checkbox_group (`Not applicable`/`Same as 16e`/`Other`) | `16g_nonorganic_records` (+ `_other`) |
| 16h | Prácticas/procedimientos de monitoreo | textarea | `16h_monitoring_practices` |
| 16i | Cómo/con qué frecuencia se implementan | textarea | `16i_monitoring_frequency` |
| 16j | Descripción de programa de prevención de fraude orgánico | textarea | `16j_fraud_prevention_program` |
| 16k | Documentos mantenidos para prevención de fraude | textarea | `16k_fraud_prevention_docs` *(adjunto diferido)* |
| 16l | Monitoreo de efectividad del programa anti-fraude | textarea | `16l_fraud_prevention_monitoring` |

---

## Sección 17: Trace back and Mass Balance — sin campos

Solo texto explicativo/informativo (qué es un traceback, qué es un mass balance, referencias NOP). **No requiere ningún input.** Se puede renderizar como texto estático en el template.

---

## Sección 18: Affirmation (Firma) — ✅ construida

Contiene: afirmaciones legales (texto fijo), Nombre de quien completa el OSP, Firma electrónica, Fecha. **Nota:** no verifiqué los `name` exactos de estos 3 campos contra el código actual — antes de tocarla, revisar `osp_form_crop.xml` directamente para confirmar nomenclatura ya usada.

---

## Sección 19: Field History Affidavit — ⏳ (condicional + tabla)

*Solo aplica si se agregaron campos nuevos a la certificación.*

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| — | Farm/Producer Name | text | `19_farm_producer_name` | |
| — | Field name/ID number | text | `19_field_id` | |
| — | Transition Start Date | date | `19_transition_start_date` | |
| — | ¿Manejó este campo 3+ años? | radio_yn | `19_managed_3years` | |
| — | Declaraciones firmadas adjuntas (si no) | radio_yn | `19_statements_attached` | adjunto diferido, condicional |
| — | ¿Campo actualmente certificado? | radio_yn | `19_field_certified` | si sí: adjunta certificado y **no** completa la tabla (lógica condicional) |
| — | Última sustancia prohibida: marca/ingrediente activo | text | `19_last_substance_brand` | |
| — | Fecha de última aplicación | date | `19_last_substance_date` | |
| — | **Tabla por año** | **table** | `19_history_json` | columnas: `year`, `crops`, `inputs_used` |
| — | Nombre del Operador | text | `19_operator_name` | |
| — | Fecha | date | `19_operator_date` | |

---

## Sección 20: Search Record – Commercial Availability of Seed and Planting Stock — ⏳ (tabla dinámica)

El PDF muestra el ejemplo con 3 filas numeradas (1, 2, 3), pero **se confirma que es dinámica** (agregar/quitar fila) igual que las demás 8 tablas — no fija en 3.

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 20 | **Tabla Search Record** | **table** | `20_search_record_json` | columnas: `crop` (texto), `traits` (texto), `why_not_met` (texto — "Why is the crop specification not met by an equivalent variety?"), `suppliers_contacted` (texto), `date_contacted` (date), `method_of_contact` (texto) |

---

## Marcadores de "adjunto pendiente" (nuevos campos por la respuesta #5)

Estos son los puntos del PDF donde se pide "Attach X" **sin** una pregunta Sí/No que ya funcione como identificador. Se agrega un campo booleano nuevo (marcador informativo, no sube archivo real todavía):

| Sección | Instrucción del PDF | JSON key nuevo | Condicional a |
|---|---|---|---|
| 1l | Attach a copy of your current State certificate | `1l_certificate_attachment_needed` | `1l_state_registration` = Yes |
| 2a | Provide all documentation (certificador que negó/suspendió) | `2a_documentation_attachment_needed` | `2a_denied_certification` = Yes |
| 2b | Attach a copy of your current organic certificate | `2b_certificate_attachment_needed` | `2b_certified_elsewhere` = Yes |
| 2c | Attach a copy of your previous organic certificate | `2c_certificate_attachment_needed` | `2c_previously_certified` = Yes |
| 2d | Attach documentation que verificó no-conformidades atendidas | `2d_documentation_attachment_needed` | — |
| 6n | Attach residue analysis and/or salinity test results | `6n_test_results_attachment_needed` | — (si aplica) |
| 7b | Submit signed statements from previous land manager | `7b_statements_attachment_needed` | `7b_managed_3years` = No |
| 8a | Submit supporting documents (semillas) | `8a_seeds_attachment_needed` | — |
| 9d | Attach copies of available test results | `9d_test_results_attachment_needed` | — |
| 9k | Submit supporting documentation (estiércol crudo + consumo humano) | `9k_documentation_attachment_needed` | condicional a selección en 9k |
| 9o | Attach residue analysis/additive specifications | `9o_analysis_attachment_needed` | — |
| 15a | Attach a flow chart and a floor plan | `15a_diagrams_attachment_needed` | — |
| 15e | Attach documented evidence (empaque libre de fungicida) | `15e_evidence_attachment_needed` | — |
| 15r | Attach label (formulación de cloro) | `15r_label_attachment_needed` | `15r_use_chlorine` = Yes |
| 15s | Attach label o spec sheet del test kit | `15s_test_kit_attachment_needed` | — (si aplica) |
| 16e | Submit a supporting document con la lista de registros | `16e_supporting_document_attachment_needed` | opcional |
| 16k | Submit los documentos de prevención de fraude | `16k_documents_attachment_needed` | — |
| 19 | Submit a copy of your certification (campo ya certificado) | `19_certification_attachment_needed` | `19_field_certified` = Yes |

*Nota: 15m ("Master Supply Chain and Product List") no genera campo nuevo — hace referencia al mismo documento ya cubierto por `5b_supply_chain_attached`, no es un adjunto distinto.*

## Preguntas abiertas — estado final

1. ~~Dropdowns "Choose an item"~~ → ✅ resuelto: se extrajeron las 12 listas reales directo del `.docx` original (controles de contenido `dropDownList`/`comboBox`). Ya están incorporadas en las filas correspondientes de arriba (1k, 1s, 1t, 1u×2, y las columnas select de las tablas 4h, 8a, 8g, 12a, 14a, 15i). **Convención confirmada:** el Word original trae errores tipográficos ocasionales (ej. `Legal Patnership` → `Legal Partnership`, `Perrenial Treatment` → `Perennial Treatment`) — el sistema siempre muestra la versión corregida, no el texto tal cual viene en el documento fuente.
2. ~~`1o_months_production`~~ → ✅ resuelto: texto libre.
3. ~~Sección 20~~ → ✅ resuelto: tabla dinámica como las demás.
4. ~~Campos condicionales~~ → ✅ resuelto: se ocultan con JS mientras el padre no sea "Yes".
5. ~~Adjuntos~~ → ✅ resuelto: se deja campo marcador `_attachment_needed` donde no existía ya una pregunta Sí/No equivalente (ver tabla arriba).

**Con esto, las 5 preguntas abiertas quedan cerradas** — ya se puede programar cualquier sección del formulario sin ambigüedades pendientes.
