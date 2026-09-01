# Especificación técnica — Formulario "Handler (Trader)" (Organic System Plan)

> ✅ **ESTADO: FORMULARIO COMPLETO CONSTRUIDO** (18/ago) — las 10 secciones y las 2 tablas dinámicas (`4a_sites_json`, `5d_products_json`) están implementadas en `views/osp_form_handler_trader.xml` + `static/src/js/osp_form.js` (`TABLE_CONFIGS.trader_sites`/`trader_products`). Reporte PDF: `report/osp_handler_trader_report_data.py` + `get_handler_trader_report_sections()` (`report/osp_handler_trader_report.py`), sobre el motor genérico compartido. Ver `CONTEXT.md` §19 para el detalle de arquitectura. El propio Word trae una nota introductoria: **"This OSP is to be completed for operations requesting organic certification without a physical facility."** — se muestra como texto informativo al inicio del formulario web.

Fuente: `Handler (Trader).docx` (PrimusAuditingOps), **10 secciones**. `technical_code` reservado: `form_handler_trader` (ya sembrado en `data/osp_form_template_data.xml`).

## Convenciones (idénticas a Crop/Handler)

Mismo formato que `FORM_SPEC_HANDLER.md`. Reutiliza literalmente las mismas JSON keys de Crop/Handler donde el texto es idéntico (Secciones 1–3).

---

## Encabezado

Nota informativa fija (sin campo): *"This OSP is to be completed for operations requesting organic certification without a physical facility."*

Choose one: First time / Update → `1_applicant_type` (igual que Crop/Handler).

---

## Sección 1: General Information — igual que Handler, con una letra fantasma

Idéntica a la Sección 1 de Handler (1a–1r) **excepto** que el Word de Trader **salta directo de `1r` a `1t`** — la letra `1s` no existe en ningún lado del documento (ni la pregunta "produce or handle", que aquí sí está pero lleva la letra `1t`, ni ninguna otra). Es un hueco real en la numeración del Word fuente (visto también en Crop/Handler con typos menores) — se respeta tal cual, sin inventar una pregunta para rellenar `1s`.

| # | Pregunta | Tipo | JSON key |
|---|---|---|---|
| 1a–1r | *(idénticas a Handler)* | — | mismas keys que Handler: `1a_org_name` ... `1r_documentation_language` |
| 1t | What does your operation produce or handle | select | `1t_produce_or_handle` (`Organic & Non-Organic Product` / `Organic Only`) |
| 1u | Driving directions / GPS confirmation | textarea | `1u_directions` |
| 1u | When available to contact / for inspection | select×2 | `1u_available_contact`, `1u_available_inspection` |
| 1v | Income ≤ $5,000/año + reventa como orgánico (condicional) | radio_yn×2 | `1v_income_5000_or_less`, `1v_resell_as_organic` |
| 1w | ¿Es renovación? + resumen de cambios (condicional) | radio_yn + textarea | `1w_is_renewal`, `1w_changes_summary` |
| 1x | Auto-auditoría + fecha (condicional) | radio_yn + date | `1x_self_audit`, `1x_self_audit_date` |

Nota: aquí las letras SÍ coinciden con las de Crop (1t/1u/1v/1w/1x), a diferencia de Handler que las tenía una posición antes (1s/1t/1u/1v/1w) — cada formulario respeta su propia numeración del Word, no hay una única convención "universal" de letras entre formularios.

---

## Sección 2 y 3 — texto IDÉNTICO a Crop/Handler

Mismas keys: `2_na`, `2a_denied_certification`, `2a_certifier_and_docs` (+ `2a_documentation_attachment_needed`), `2b_certified_elsewhere` (+ `2b_certificate_attachment_needed`), `2c_previously_certified` (+ `2c_certificate_attachment_needed`), `2d_noncompliances_na`, `2d_noncompliances_details` (+ `2d_documentation_attachment_needed`), `3_na`, `3a_market_types`.

---

## Sección 4: Operation Information (205.201, 205.401) — más corta que la de Handler (no hay facility)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 4a | ¿Maneja otras oficinas/sitios además de la dirección de la Sección 1? | radio_yn | `4a_other_sites` | |
| 4a | **Tabla de sitios** (si sí) | **table** | `4a_sites_json` | columnas: `site_id`, `site_address` (campo único "Address: City, State, Zip" — el Word lo trae combinado, a diferencia de Handler que lo separaba en 3 campos), `contact`, `description` |
| 4b | Operation Flow Diagram Attached | radio_yn | `4b_flow_diagram_attached` | el Yes/No ya funciona como identificador |
| 4c | % proyectado producción orgánica/no-orgánica | text×2 | `4c_pct_nonorganic`, `4c_pct_organic` | *(si maneja no-orgánico, instrucción de enviar lista — sin Yes/No asociado)* attachment marker `4c_nonorganic_list_attachment_needed` (sin condicional, siempre visible — igual criterio que otros "submit a list" sin Sí/No previo) |
| 4d | ¿Tiene certificaciones además de Orgánico? | radio_yn | `4d_other_certifications` | si sí: `4d_other_certifications_details` (texto) |

---

## Sección 5: Products – To Be Listed on Certificate by ID Mark & Market — como Handler, MENOS 1 columna

Igual que Handler salvo que la tabla `5d` **no tiene** la columna "¿Empacará con este ID Mark?" (tiene sentido: un trader típicamente no re-empaca).

| # | Pregunta | Tipo | JSON key | Opciones |
|---|---|---|---|---|
| 5a | Type of Marketing | checkbox_group | `5a_marketing_types` (+ `5a_marketing_other`) | idéntico a Handler |
| 5b | Master Supply Chain doc adjunto | radio_yn | `5b_supply_chain_attached` | |
| 5c | ¿Requiere que el certificado liste todos los ID Marks? | radio_yn | `5c_list_all_id_marks` | |
| 5d | **Tabla Products** (SIN columna "packing_with_id") | **table** | `5d_products_json` | columnas: `product`, `id_mark`, `label_type` (texto libre: Retail/Non-Retail/Private Label), `organic_or_100` (texto libre), `international_market` (texto) |

---

## Sección 6: Biodiversity & Natural Resources — ⚠️ VER "Punto a confirmar" abajo

| # | Pregunta | Tipo | JSON key |
|---|---|---|---|
| 6a | Programa de biodiversidad | textarea | `6a_biodiversity_program` |
| 6b | Recursos naturales dentro/alrededor de la operación | textarea | `6b_natural_resources` |
| — | *Waste Management* | — | — |
| **6c** | Prácticas de manejo de residuos | textarea | `6c_waste_management` |
| **6d** | ¿Recicla materiales? + Describa | radio_yn + textarea | `6d_recycle_waste`, `6d_recycle_describe` |
| — | *Energy Conservation & Air Quality* | — | — |
| **6e** | Prácticas de conservación de energía | textarea | `6e_energy_conservation` |
| **6f** | Prácticas de calidad del aire | textarea | `6f_air_quality` |
| — | *Water Use* — Not applicable to my operation | checkbox | `6_water_use_na` |
| 6g | Fuente de agua | text | `6g_water_source` |
| 6h | ¿Análisis de agua adjunto? + nombre del documento | radio_yn + text | `6h_water_analysis_attached`, `6h_water_analysis_doc_name` |
| 6i | Prácticas de conservación de agua | textarea | `6i_water_conservation` |
| 6j | ¿En qué capacidad se usa el agua? | text | `6j_water_use_capacity` |

---

## Sección 7: Maintenance of Organic Integrity (205.270, 205.272, 205.300, 205.101(b), 205.605)

Combina en una sola sección lo que en Handler eran 3 secciones separadas (Storage/Post-Harvest, Equipment/Sanitation, Packaging) — sin equipo/sanitización porque un trader no maneja físicamente el producto.

**Storage & Shipping** — checkbox N/A (`7_storage_na`):
| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 7a | Describa las operaciones utilizadas para almacenamiento | textarea | `7a_storage_operations` | nota informativa: "Must complete the Master Supply Chain and Product list" (ya cubierto por 5b, sin marcador nuevo) |
| 7b | ¿Su organización es responsable del transporte? | radio_yn | `7b_responsible_for_transport` | si sí: `7b_transport_company` (texto — "list the company") |
| 7c | ¿En qué forma se reciben los productos orgánicos? | text | `7c_receiving_form` | |
| 7d | ¿En qué forma se envían los productos terminados? | text | `7d_shipping_form` | |

**Quality Testing** — checkbox N/A (`7_quality_na`):
| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 7e | ¿Se muestrean productos/ingredientes para calidad o pruebas? | radio_yn | `7e_products_sampled` | |
| 7e | ¿Herramientas de muestreo dedicadas solo a orgánico? | radio_yn | `7e_tools_dedicated` | condicional a 7e=Yes |
| 7e | Si no, describa limpieza del equipo / adjunte procedimiento | textarea | `7e_cleaning_description` | condicional a `7e_tools_dedicated`=No |

**Packaging** — checkbox N/A (`7_packaging_na`):
| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 7f | Tipo de material de empaque | text | `7f_packaging_material_type` | |
| 7g | ¿Empaque libre de fungicida/preservante/fumigante sintético? | radio_yn | `7g_free_of_synthetics` | si no: `7g_explain` (textarea); si sí: marker `7g_evidence_attachment_needed` |
| 7h | Tipo de empaque usado (aséptico, cartón, vidrio, etc.) | text | `7h_packaging_type` | pregunta separada de 7f en el Word (aunque se ven parecidas, se respetan ambas tal cual vienen) |
| 7i | ¿Todo el empaque es food grade? | radio_yn | `7i_food_grade` | |
| 7j | ¿Materiales/contenedores de empaque se reutilizan? | radio (`Yes`/`No`/`N/A`) | `7j_reused` | **a diferencia de Handler (11c), aquí el Word SÍ trae el control Yes/No/N-A** |
| 7j | Si sí, uso previo | textarea | `7j_previous_use` | condicional a Yes |
| 7j | Procedimiento de limpieza antes de reutilizar | textarea | `7j_cleaning_procedure` | condicional a Yes |

---

## Sección 8: Record-Keeping System (205.103, 205.400)

| # | Pregunta | Tipo | JSON key | Notas |
|---|---|---|---|---|
| 8a | Cómo los registros rastrean el producto hasta la última operación certificada | textarea | `8a_traceback_description` | |
| 8b | Cómo asegura que el # de lote/ID de envío vincule el contenedor/producto con la documentación de auditoría | textarea | `8b_lot_tracking` | |
| 8c | ¿Registros identifican el reclamo aplicable (100% orgánico, etc.)? | radio_yn | `8c_claim_identification` | **el Word SÍ trae Yes/No aquí** (a diferencia del 13d de Handler) |
| 8c | Si no, cómo identifica orgánico vs no-orgánico | textarea | `8c_identification_explain` | condicional a No |
| 8d | Qué registros mantiene para producción orgánica | textarea | `8d_organic_records` | |
| 8e | ¿Registros mantenidos 5+ años? | radio_yn | `8e_records_5years` | |
| 8f | Qué registros mantiene para producción no-orgánica | checkbox_group | `8f_nonorganic_records` (+ `_other`) | `Not applicable, organic only` / `Same as the records listed in 8d` / `Other` |
| 8g | Prácticas/procedimientos de monitoreo | textarea | `8g_monitoring_practices` | |
| 8h | Cómo/con qué frecuencia se implementan | textarea | `8h_monitoring_frequency` | |
| 8i | Programa de prevención de fraude orgánico | textarea | `8i_fraud_prevention_program` | |
| 8j | Documentos mantenidos para fraude (y enviarlos) | textarea | `8j_fraud_prevention_docs` | attachment implícito |
| 8k | Monitoreo de efectividad del programa anti-fraude | textarea | `8k_fraud_prevention_monitoring` | |

---

## Sección 9: Trace back and Mass Balance — sin campos

Texto idéntico (palabra por palabra) al de la Sección 14 de Handler / 17 de Crop. Estático.

---

## Sección 10: Affirmation (Firma)

Mismo texto legal que Handler/Crop. **A diferencia de Handler, aquí el Word SÍ trae los 3 campos completos** (Name, Signature, Date) — no hace falta agregar Date artificialmente.

| Campo | Tipo | JSON key |
|---|---|---|
| Name of Person completing this OSP | text | `10_name` |
| Signature of Authorized Person | text | `10_signature` |
| Date | date | `10_date` |

---

## Marcadores de "adjunto pendiente"

| Sección | Instrucción del Word | JSON key nuevo | Condicional a |
|---|---|---|---|
| 1l | Attach a copy of your current State certificate | `1l_certificate_attachment_needed` | `1l_state_registration` = Yes |
| 2a | Provide all documentation | `2a_documentation_attachment_needed` | `2a_denied_certification` = Yes |
| 2b | Attach a copy of your current organic certificate | `2b_certificate_attachment_needed` | `2b_certified_elsewhere` = Yes |
| 2c | Attach a copy of your previous organic certificate | `2c_certificate_attachment_needed` | `2c_previously_certified` = Yes |
| 2d | Attach documentation que verificó no-conformidades atendidas | `2d_documentation_attachment_needed` | — |
| 4c | Submit a list of the non-organic product handled | `4c_nonorganic_list_attachment_needed` | — (sin Sí/No previo en el Word) |
| 7g | Attach documented evidence | `7g_evidence_attachment_needed` | `7g_free_of_synthetics` = Yes |

## Punto resuelto (confirmado con el usuario, 18/ago)

**Sección 6 del Word tenía las letras `6c`-`6f` usadas DOS VECES** (Waste Management/Energy Conservation, y luego otra vez para Water Use) — error real de numeración del documento original. **Decisión confirmada**: se continúa la numeración natural para el segundo grupo — Water Use usa `6g`-`6j` (letras que el Word no usaba en ningún otro lado de esta sección), en vez de repetir `6c`-`6f`. Ya incorporado en la tabla de la Sección 6 de arriba.

**Con esto la spec queda cerrada — no hay preguntas pendientes.** El resto del formulario no tiene ambigüedades (hereda las convenciones ya confirmadas en Crop/Handler: selects reales para State/Country, tal cual viene el Word para los controles Sí/No/N-A que sí trae, etc.). Ya se puede programar.
