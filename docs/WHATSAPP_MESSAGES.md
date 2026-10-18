# Mensajes de pedidos por WhatsApp — 18/10/2026

Editar desde Admin → Configuración comercial → Mensaje de WhatsApp. Se conservan saludo y formatos personalizados; guardar actualiza la vista previa. El texto sigue siendo configurable y el usuario decide enviarlo en WhatsApp.

## Formato inicial vigente

Mensaje general:

````text
Hola! Quisiera realizar el siguiente pedido 🛍️:

{productos}

────────────

*💰 Total: {total}*

📌 Los precios y la disponibilidad de los productos se confirmarán al procesar el pedido.
````

Producto:

```text
*{numero}. {producto}*
Marca: {marca}
Cantidad: {cantidad_presentacion}
Presentación: {presentacion_adicional}
Precio: {precio} por {unidad_precio}
*Subtotal: {subtotal}*
```

Marca y Presentación se omiten si están vacías. Negrita de WhatsApp usa un asterisco a cada lado, sin HTML. No hay divisores repetidos por artículo ni etiquetas de tarifa. Nombres/marca/descripción neutralizan marcadores de estilo como antes, sin modificar los datos guardados. Mensaje, copiado y enlace usan el texto calculado por Django, sin recalcular importes en el navegador.

## Campos

| Campo | Contenido |
| --- | --- |
| `{productos}` / `{total}` | Listado completo / total en pesos enteros, obligatorios en general |
| `{numero}` / `{producto}` | Posición en carrito / título, sin categoría |
| `{marca}` | Marca registrada en el producto; vacía no agrega línea |
| `{cantidad_presentacion}` | Ej. 3 porciones de 100 g, 2 kg, 4 packs de 3 paquetes de 500 g |
| `{unidad_precio}` | 100 g, kg, caja, pack, paquete, bolsa; unidad antigua conservada |
| `{presentacion_adicional}` | Descripción que no se pudo integrar con certeza; vacía cuando sería repetitiva |
| `{precio}` / `{subtotal}` | Minorista vigente / subtotal exacto; símbolo $ y separadores argentinos, sin centavos |
| `{cantidad}` / `{unidad}` / `{descripcion}` | Compatibilidad: cantidad numérica, unidad original y descripción original; no cambiaron su significado |

Conservar producto, precio, subtotal y una combinación de campos que identifique cantidad/unidad. Sin acceso a atributos, conversiones ni formatos de Python. Llaves literales con `{{`/`}}`. Campos desconocidos o pérdida de datos obligatorios se rechazan. Una línea sólo de campos opcionales vacíos se omite; si contiene datos obligatorios nunca se oculta.

## Presentaciones y límite de datos

No existe contenido estructurado independiente de Product.description. Se reconocen exclusivamente expresiones completas de peso (500 gr, Paquete de 500 gr, Caja de 5 kg, Bolsa de 2 kg) o composición (Pack de 3 paquetes de 500 gr); mayúsculas, espacios y punto final se normalizan al mostrar. gr/g se muestran como g. No multiplicar el peso o la composición por la cantidad elegida: tres cajas de 5 kg siguen siendo tres cajas de 5 kg.

Descripción vacía: sólo cantidad y unidad. Texto fuera de esas formas (Caja individual para regalo, Pack de 3 cajas para regalo, Caja de 5 kg o 10 kg, indicaciones adicionales) se conserva literalmente en Presentación; no se intenta adivinar ni borrar contenido. Para 100 gr siempre es porción/porciones de 100 g; descripción redundante se omite. Venta por kilogramo se omite para kg. Unidades anteriores unidad/unidades compatibles. Sólo enteros desde 1, como el carrito actual; no se habilitan fracciones nuevas.

## Emojis y apertura

Se reprodujo con texto ficticio y número no comercial: wa.me redirigió 🛍️/💰/📌 como U+FFFD; tanto espacios + como %20 sufrieron el mismo problema. El endpoint directo de WhatsApp mantuvo el texto exacto en su enlace a WhatsApp Web. Por eso se usa `https://api.whatsapp.com/send?phone=...&text=...`: click-to-chat público, sin Cloud API ni envío automático.

Un único urlencode con quote, UTF-8 estricto, safe vacío y espacios %20. Preservar emojis compuestos/ZWJ/banderas, ñ, acentos, +, %, &, saltos de línea y estilos. Sin encode/decode adicional en JavaScript. [Funcionamiento de clic para chatear](https://faq.whatsapp.com/5913398998672934/?locale=es_LA) y [codificación de componentes en Python](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlencode).

La pestaña provisional y el enlace manual comparten el destino revalidado; cerrar/cancelar/fallo/cambio de catálogo impide navegación pendiente como antes. No se envió un pedido real durante las pruebas. Verificar envío/visualización final en la instalación de WhatsApp del usuario sigue requiriendo su acción.

## Migración y aplicación local

0009 modifica defaults/ayuda del formato y reemplaza sólo los textos iniciales conocidos de BusinessSettings. Respeta formatos personalizados exactos, productos, presentaciones, precios, fotos, usuarios, horarios y demás configuración. Reversa de datos noop para no deshacer ediciones posteriores. No hay nuevos campos, modelos o dependencias.

Aplicada sólo en esta PC con respaldo privado de configuración en .qa/backups/20261018-whatsapp-format/business-settings-before.json y comparación exacta posterior. 45 fichas, fotos/manifiesto, precios, usuarios, horarios y categorías intactos; sólo los dos defaults locales cambiaron. Para otra instalación autorizada: respaldar configuración, actualizar código, ejecutar migrate/check y recargar. No desplegar en Raspberry ni cambiar infraestructura como parte de esta tarea.


## Archivos de esta modificación

- catalog/whatsapp.py: enlace directo UTF-8 y valores derivados compartidos por Admin/revisión/copia/WhatsApp.
- catalog/whatsapp_presentations.py: seis unidades, pluralización, contenido completo reconocido y fallback conservador.
- catalog/whatsapp_templates.py: defaults/aliases/validación y omisión de líneas opcionales vacías.
- catalog/models.py: ayuda de campos del formato en Admin; migración 0009_whatsapp_readable_format.py con defaults versionados y reemplazo conservador.
- catalog/test_whatsapp.py, test_whatsapp_unicode.py, test_whatsapp_presentations.py, test_message_templates.py, test_presentations.py, test_subtotal_migration.py, test_integer_prices.py y tests/browser.spec.cjs: regresiones de texto/Unicode/formatos/migraciones, sin alterar validaciones o cálculos del carrito.
- README y docs/PRODUCT_SPEC.md, ARCHITECTURE.md, UX_UI.md, ROADMAP.md, QA.md, EXECUTION_STATUS.md y este documento: decisión, límites, evidencia y pasos.

Validación final: 203 Django, 9 Node y 84 Chromium; check/Ruff/migraciones/diff correctos. QA retirado, base local con 45 fichas y 0009 aplicada; Ctrl+F5. Cambios concretos revisados, sin commit/push ni publicación.
