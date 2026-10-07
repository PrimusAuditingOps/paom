# PAO Sale Combo

Combos de productos con precio por lista de precios, que se agregan a la cotización como una sección.
Solo disponible para compañías con país **Chile**.

## 1. Catálogo de combos

**Ventas › Configuración › Combos**

- Nombre del combo (p. ej. "GLOBALG.A.P. Opción 1 + Nurture") y sus productos, en el orden en que se
  agregarán a la cotización.
- Un mismo producto puede estar en varios combos; en un mismo combo solo una vez.
- Cantidad: siempre 1 por producto.

## 2. Precios del combo en la lista de precios

**Lista de precios › pestaña Combos** (junto a "Reglas de precio"; visible si la lista es de una compañía de Chile,
o sin compañía y la compañía activa es Chile).

- Agregar un combo abre una ventana con sus productos; a cada uno se le pone su precio unitario.
- El mismo producto puede tener precios distintos en combos distintos.
- Si después se agregan o quitan productos del combo en el catálogo, el botón **Actualizar productos desde el combo**
  alinea la lista (los nuevos empiezan en 0, los existentes conservan su precio).

## 3. Agregar combo en la cotización

En las líneas de la cotización, junto a "Agregar un producto", el botón **Agregar combo** (solo en compañías de Chile):

1. Se elige el combo (la ventana avisa si el combo no está en la lista de precios de la cotización).
2. Se agrega al final una **sección** con el nombre del combo y debajo sus productos (cantidad 1).
3. Precio unitario de cada producto:
   - el precio del combo en la lista de precios de la cotización;
   - **0** si el combo no está en esa lista, o si el producto no tiene precio en ese combo.

Cada línea guarda de qué combo viene (columna opcional **Combo** en las líneas). Por eso, si se cambia la cantidad
o se usa **Actualizar precios** (p. ej. al cambiar la lista de precios), la línea vuelve a tomar el precio del combo
en lugar del precio normal de la lista. Las líneas de combo no reciben descuentos automáticos de la lista de precios.
Igual que en Odoo nativo, una línea que ya tiene cantidad facturada no se recalcula.

## Detalle técnico

- Modelos: `pao.sale.combo` / `pao.sale.combo.line` (catálogo), `pao.pricelist.combo` / `pao.pricelist.combo.line`
  (precios por lista), `pao.sale.combo.add` (asistente). Campo `pao_combo_id` en `sale.order.line`.
- `sale.order.line._compute_price_unit` / `_compute_discount` se extienden solo para las líneas con combo.
- `static/src/views/list_renderer_patch.*`: en Odoo 17 los botones dentro de `<control>` de una lista x2many
  ignoran `invisible`; el parche lo evalúa (con acceso a `parent`) para mostrar "Agregar combo" solo en Chile.
