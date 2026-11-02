# Especificación técnica — Formulario "Comercializador" (Organic System Plan)

> ✅ **ESTADO: FORMULARIO COMPLETO CONSTRUIDO** (18/ago) — las 10 secciones y las 2 tablas dinámicas (`4a_sites_json`, `5d_products_json`) están implementadas en `views/osp_form_comercializador.xml` + `static/src/js/osp_form.js` (`TABLE_CONFIGS.comercializador_sites`/`comercializador_products`). Reporte PDF: `report/osp_comercializador_report_data.py` + `get_comercializador_report_sections()` (`report/osp_comercializador_report.py`). Ver `CONTEXT.md` §23. **Formulario nativo en español**, equivalente casi exacto de `FORM_SPEC_HANDLER_TRADER.md`.

Fuente: `Comercializador.docx` (PrimusAuditingOps), **10 secciones**. `technical_code` reservado: `form_comercializador` (ya sembrado en `data/osp_form_template_data.xml`).

## Decisiones heredadas (no se vuelven a preguntar)

1. **Estado/País como selects reales**, aunque el Word traiga texto libre.
2. **Letra `1s` no existe en el Word** (salta de `1r` a `1t`, igual que en Handler (Trader)) — se respeta tal cual, sin inventar la pregunta faltante.
3. **Sección 6 repite las letras `6c`-`6f` dos veces** (Gestión de Residuos/Conservación de Energía, y luego otra vez para Uso de Agua) — mismo bug de numeración ya visto en Handler (Trader). **Se aplica la misma decisión ya confirmada**: el segundo grupo (Uso de Agua) usa `6g`-`6j` en vez de repetir letras.
4. **Sección 6 no tiene checkbox de "N/A" al inicio** (a diferencia de Handler-Trader que sí lo tenía en "Water Use") — se respeta tal cual el Word, sin agregar uno.
5. **7g solo trae 2 opciones (Sí/No)**, no 3 como en Handler — se respeta tal cual.
6. **Nombre, Firma y Fecha completos en la Sección 10** — el Word sí trae los 3 campos, no hace falta agregar Fecha manualmente (igual que Trader).

---

## Encabezado

Nota introductoria fija: *"Este OSP debe ser completado para operaciones que solicitan certificación orgánica sin una instalación física."*

Seleccione una opción: Primera aplicación / Actualización → `1_applicant_type`.

---

## Sección 1: Información General — igual que Handler (Trader), sin letra 1s

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 1a–1r | *(idénticas a Manejo o Proceso/Handler)* | — | `1a_org_name` ... `1r_documentation_language` | |
| 1t | Qué produce o manipula su empresa | select | `1t_produce_or_handle` | opciones: `Solamente Orgánico` / `Orgánico y No-Orgánico` (orden invertido vs. otros formularios, pero mismo par de opciones — sin ambigüedad, coincide con el texto de la pregunta) |
| 1u | Indicaciones de ubicación / GPS | textarea | `1u_directions` | |
| 1u | Horario disponible contactar / inspección | select×2 | `1u_available_contact` (`Mañana`/`Tarde`/`Noche`/`Cualquier tiempo`), `1u_available_inspection` (`Mañana`/`Tarde`/`Cualquier tiempo`) | |
| 1v | Ingreso ≤ $5,000 + reventa (condicional) | radio_yn×2 | `1v_income_5000_or_less`, `1v_resell_as_organic` | |
| 1w | ¿Renovación? + resumen (condicional) | radio_yn + textarea | `1w_is_renewal`, `1w_changes_summary` | |
| 1x | Auto-auditoría + fecha (condicional) | radio_yn + date | `1x_self_audit`, `1x_self_audit_date` | |

---

## Sección 2 y 3 — mismo contenido que los demás formularios

Mismas keys: `2_na`, `2a_denied_certification`, `2a_certifier_and_docs` (+ marker), `2b_certified_elsewhere` (+ marker), `2c_previously_certified` (+ marker), `2d_noncompliances_na`, `2d_noncompliances_details` (+ marker), `3_na`, `3a_market_types`. Sección 3 con la misma nota extra sobre Canadá.

---

## Sección 4: Información de la operación — igual que Handler (Trader) Sección 4

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 4a | ¿Gestiona otros sitios? | radio_yn | `4a_other_sites` | |
| 4a | **Tabla de sitios** (si sí) | **table** | `4a_sites_json` | columnas: `site_id`, `site_address` (combinado, igual que Trader), `contact`, `description` — 4 columnas |
| 4b | Diagrama de flujo adjunto | radio_yn | `4b_flow_diagram_attached` | |
| 4c | % producción orgánica/no-orgánica | text×2 | `4c_pct_nonorganic`, `4c_pct_organic` | attachment marker `4c_nonorganic_list_attachment_needed` (sin Sí/No previo, igual que Trader) |
| 4d | ¿Otras certificaciones? | radio_yn + text | `4d_other_certifications`, `4d_other_certifications_details` | |

---

## Sección 5: Productos — igual que Handler (Trader)

| # | Pregunta | Tipo | JSON key | Opciones |
|---|---|---|---|---|
| 5a | Tipo de mercado | checkbox_group | `5a_marketing_types` (+ `_other`) | idéntico a Manejo o Proceso |
| 5b | Lista de cadena de suministro adjunta | radio_yn | `5b_supply_chain_attached` | |
| 5c | ¿Lista de marcas en certificado? | radio_yn | `5c_list_all_id_marks` | |
| 5d | **Tabla Productos** | **table** | `5d_products_json` | columnas: `product`, `id_mark`, `label_type` (texto: `Minorista`/`Mayoreo`/`Etiqueta Privada`), `organic_or_100` (texto libre), `international_market` (texto) — **decisión confirmada**: 2 campos de texto separados, igual que Handler (Trader), no combinados en uno |

---

## Sección 6: Biodiversidad y Recursos Naturales — mismo choque de letras que Trader

| # | Pregunta | Tipo | JSON key |
|---|---|---|---|
| 6a | Programa de biodiversidad | textarea | `6a_biodiversity_program` |
| 6b | Recursos naturales | textarea | `6b_natural_resources` |
| — | *Gestión de Residuos* | — | — |
| 6c | Prácticas de gestión de residuos | textarea | `6c_waste_management` |
| 6d | ¿Recicla? + Describa | radio_yn + textarea | `6d_recycle_waste`, `6d_recycle_describe` |
| — | *Conservación de Energía y Calidad del Aire* | — | — |
| 6e | Conservación de energía | textarea | `6e_energy_conservation` |
| 6f | Calidad del aire | textarea | `6f_air_quality` |
| — | *Uso de Agua* — No aplica | checkbox | `6_water_use_na` |
| 6g | Fuente de agua *(renumerado, ver decisión heredada #3)* | text | `6g_water_source` |
| 6h | Análisis de agua adjunto + nombre doc | radio_yn + text | `6h_water_analysis_attached`, `6h_water_analysis_doc_name` |
| 6i | Conservación de agua | textarea | `6i_water_conservation` |
| 6j | Capacidad de uso de agua | text | `6j_water_use_capacity` |

---

## Sección 7: Mantenimiento de la Integridad Orgánica — igual que Handler (Trader) Sección 7

**Almacenamiento y Transporte** (checkbox N/A `7_storage_na`):
- 7a `7a_storage_operations` (textarea)
- 7b `7b_responsible_for_transport` (yn) + `7b_transport_company` (condicional)
- 7c `7c_receiving_form` (text)
- 7d `7d_shipping_form` (text)

**Pruebas de Calidad** (checkbox N/A `7_quality_na`):
- 7e `7e_products_sampled` (yn) + `7e_tools_dedicated` (yn, condicional) + `7e_cleaning_description` (textarea, condicional a tools_dedicated=No)

**Envasado/Empaquetado** (checkbox N/A `7_packaging_na`):
- 7f `7f_packaging_material_type` (text)
- 7g `7g_free_of_synthetics` (yn — solo 2 opciones) + `7g_explain` (condicional No) + `7g_evidence_attachment_needed` (marker, condicional Yes)
- 7h `7h_packaging_type` (text)
- 7i `7i_food_grade` (yn)
- 7j `7j_reused` (yn_na) + `7j_previous_use` + `7j_cleaning_procedure` (condicionales a Yes)

---

## Sección 8: Sistema de Registro — igual que Handler (Trader) Sección 8

Mismas keys: `8a_traceback_description`, `8b_lot_tracking`, `8c_claim_identification` (yn, **sí presente** en el Word) + `8c_identification_explain` (condicional No), `8d_organic_records`, `8e_records_5years`, `8f_nonorganic_records` (+ `_other`), `8g_monitoring_practices`, `8h_monitoring_frequency`, `8i_fraud_prevention_program`, `8j_fraud_prevention_docs`, `8k_fraud_prevention_monitoring`.

---

## Sección 9: Trazabilidad y Balance de Masas — sin campos

Texto informativo estático (misma explicación que los demás formularios, traducida).

---

## Sección 10: Afirmación

| Campo | Tipo | JSON key |
|---|---|---|
| Nombre del Representante Autorizado | text | `10_name` |
| Firma del Representante Autorizado | text | `10_signature` |
| Fecha | date | `10_date` |

(Los 3 campos ya vienen completos en el Word — no hace falta agregar nada extra, igual que en Trader.)

---

## Marcadores de "adjunto pendiente"

| Sección | Instrucción del Word | JSON key | Condicional a |
|---|---|---|---|
| 1l | Adjunte copia del certificado Estatal | `1l_certificate_attachment_needed` | `1l_state_registration` = Yes |
| 2a | Facilite toda la documentación | `2a_documentation_attachment_needed` | `2a_denied_certification` = Yes |
| 2b | Adjuntar copia del certificado actual | `2b_certificate_attachment_needed` | `2b_certified_elsewhere` = Yes |
| 2c | Adjuntar copia del certificado anterior | `2c_certificate_attachment_needed` | `2c_previously_certified` = Yes |
| 2d | Adjuntar documentación de incumplimientos resueltos | `2d_documentation_attachment_needed` | — |
| 4c | Presentar lista de productos no-orgánicos | `4c_nonorganic_list_attachment_needed` | — (sin Sí/No previo) |
| 7g | Adjuntar pruebas documentadas | `7g_evidence_attachment_needed` | `7g_free_of_synthetics` = Yes |

## Punto resuelto (confirmado con el usuario, 18/ago)

**Tabla de Productos (Sección 5d)**: la extracción automática de las filas de datos no permitía confirmar con certeza si "Orgánico o 100%" y "Mercados Internacionales" eran 2 campos de texto separados o uno combinado. **Decisión confirmada**: se construyen como 2 campos de texto separados (`organic_or_100` e `international_market`), igual que en Handler (Trader).

**Con esto la spec queda cerrada — no hay preguntas pendientes.** Ya se puede programar el formulario completo, heredando todas las convenciones ya confirmadas en Handler (Trader)/Manejo o Proceso.
