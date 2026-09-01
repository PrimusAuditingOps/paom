# Especificación técnica — Formulario "Cultivo" (Organic System Plan)

> ✅ **ESTADO: FORMULARIO COMPLETO CONSTRUIDO** (18/ago) — **último formulario del catálogo original de 6, completando el catálogo**. Las 20 secciones y las 12 tablas dinámicas están implementadas en `views/osp_form_cultivo.xml`, reutilizando **exactamente los mismos ids de tabla/botón/campo que Crop** (sin agregar ni una sola entrada nueva a `TABLE_CONFIGS` en `osp_form.js`, porque las columnas son idénticas). Reporte PDF: `report/osp_cultivo_report_data.py` + `get_cultivo_report_sections()` (`report/osp_cultivo_report.py`). Ver `CONTEXT.md` §24. Es el equivalente en español de Crop, sección por sección y campo por campo.

Fuente: `Cultivo.docx` (PrimusAuditingOps), **20 secciones**. `technical_code` reservado: `form_cultivo` (ya sembrado en `data/osp_form_template_data.xml`) — **es el último formulario del catálogo original de 6**.

## Decisiones heredadas de Crop (no se vuelven a preguntar)

1. **Estado/País como selects reales**, aunque el Word traiga texto libre.
2. **Valores internos Sí/No en inglés** (`"Yes"`/`"No"`/`"N/A"`) aunque la etiqueta visible esté en español — misma regla ya aplicada en Manejo o Proceso/Comercializador (ver `CONTEXT.md` punto 22).
3. **Secciones 1-3, 6-20 coinciden campo por campo con Crop** (mismo texto, mismas opciones, solo traducidas). Se reutilizan exactamente las mismas JSON keys que ya existen en `FORM_SPEC_CROP.md` — no se repiten aquí letra por letra, salvo donde hay una diferencia real (ver abajo).
4. **A diferencia de Manejo o Proceso, aquí SÍ existen tanto `1s` (Tipo de operación — Zona de Cultivo Interior/Exterior/Ambas) como `1t` (¿Produce o maneja? — Solo Orgánico/Orgánico y No-Orgánico) como preguntas SEPARADAS**, igual que en Crop — no hay el error de copiado que sí tenía Manejo o Proceso. `1t` aquí usa las mismas letras que Crop (no las de Handler).
5. **Sección 18 (Afirmación) trae Nombre, Firma y Fecha completos** — no hace falta agregar nada.
6. **Corrección silenciosa de un residuo en inglés**: la pregunta `16k` del Word está sin traducir (*"List the documents you maintain for your organic fraud prevention program and submit them."*) — se traduce directamente a español ("Enumere los documentos que mantiene para su programa de prevención del fraude orgánico y envíelos.") por consistencia, mismo criterio que corregir un typo obvio.

---

## Diferencias reales de contenido vs. Crop (no ambigüedades, solo adaptaciones)

- **Tabla 8a (Semillas)**: el dropdown de `seed_type` aquí solo trae 3 opciones (`Certificada Orgánica` / `No Orgánica y No Tratada` / `No Orgánica y Tratada`), no las 6 de Crop — las 3 variantes de "Planting Stock" no aplican aquí porque la Sección 8g ya cubre ese caso por separado con su propio dropdown de 2 opciones.
- **Tabla 4a Equipo (owned_rented_custom)**: dropdown `Propio`/`Alquilado`/`Compartido` — mismo concepto que Crop (`Owned`/`Rented`/`Custom`), con "Compartido" en vez de "Custom" (más preciso semánticamente, sin ambigüedad).
- **Tabla 15i (Storage) `storage_used_for`**: 5 opciones en el mismo orden conceptual que Crop, solo reordenadas: `Orgánico`/`No Orgánico`/`Transicional`/`Amortiguamiento`/`Compartido`.

## Punto resuelto (confirmado con el usuario, 18/ago)

**Tablas 4h (Campos) y 4j (Cultivos) — unidades de medida**: aunque en el Word las casillas Acre/Hectárea aparecen una sola vez a nivel de encabezado (sugiriendo una sola unidad para toda la tabla), **decisión confirmada: igual que Crop** — cada fila mantiene su propio select de unidades (`area_units`, `yield_units`), reutilizando exactamente el mismo componente ya probado, sin inventar un patrón nuevo.

**Con esto la spec queda cerrada — no hay preguntas pendientes.** Dado lo extenso del formulario (20 secciones, ~300 preguntas, 12 tablas), la spec detallada campo por campo se construye reutilizando literalmente las keys ya definidas en `FORM_SPEC_CROP.md` (mismo mapeo sección por sección documentado arriba) directamente durante la programación, en vez de retranscribirlas aquí una por una. Ya se puede programar.
