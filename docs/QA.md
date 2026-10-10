# QA del MVP — 2026-10-10

## Validación ejecutada

- Docker: Python 3.12, Django 5.2.18 y PostgreSQL 16; migraciones 0001/0002 aplicadas.
- `python manage.py check`: sin errores.
- `python manage.py test`: 42 tests correctos.
- `python manage.py makemigrations --check --dry-run`: sin cambios.
- `ruff check .`: correcto.
- `node --test tests/*.test.cjs`: 4 tests correctos.
- `node --test tests/browser.spec.cjs`: 11 comprobaciones correctas en Chromium, incluidos 10 escenarios del flujo.
- axe WCAG 2 A/AA y 2.1 AA: cero infracciones automáticas en catálogo, carrito, revisión y carrito vacío.
- Capturas revisadas: catálogo a 360, 390, 430 y 1280 px, carrito/revisión móvil. Sin desbordamiento horizontal; controles de al menos 44 px.

La primera ejecución de navegador detectó contraste insuficiente en el marcador de imagen ausente. Se corrigió junto al contenedor de fotos. También se corrigieron selectores ambiguos del test y la codificación de la página que intercepta WhatsApp; los escenarios completos se volvieron a ejecutar. Se verificó luego cancelación durante consultas, unidad cambiada, sincronización entre pestañas y almacenamiento bloqueado. No quedan fallos de estas suites.

## Criterios de aceptación

| Criterio de PRODUCT_SPEC | Evidencia |
| --- | --- |
| Navegación/búsqueda sin cuenta, sólo activos | Tests Django de búsqueda/categorías/estados y escenario Chromium |
| Cantidad, tarifa manual y condición | Validación de modelos y carrito; escenarios minorista/mayorista y cambio de unidad |
| Persistencia al cerrar/reabrir | Chromium cierra la pestaña y abre otra con el mismo almacenamiento |
| Precios vigentes y cambios comunicados | Tests de cambios de precio, mayorista retirado, categoría/producto inactivo y revalidación final |
| Precisión monetaria | Decimal, redondeo mitad hacia arriba, suma de subtotales; 0,1 × 10,25 = 1,03; dos renglones = 2,06 |
| Advertencia y cancelación | Diálogo con texto exacto, Escape, volver y cancelación durante consulta final |
| Mensaje completo | Codificación URL, marca opcional, cantidades/unidades/tarifa, subtotales/total, mensaje largo sin truncar |
| Admin e imágenes | Auth/permisos, creación de modelos, tipo real, tamaño/dimensiones, WebP, orientación, transparencia, metadata y limpieza |
| Uso móvil/teclado | Anchuras móviles, foco inicial del diálogo, Escape, etiquetas/foco visible y axe; lector real pendiente |
| Sin pedidos/stock | Sólo Category/Product y modelos estándar Django; carrito local y cálculos stateless |

## Aislamiento y CI

El servidor `tests/browser_server.py` crea una base PostgreSQL con nombre `dulce_salado_qa_<aleatorio>` y media temporal. Los productos, precios, administrador y teléfono son fixtures descartables de test. La base comercial se comprobó vacía (0 productos, 0 categorías). Tras detener el contenedor QA, la consulta de bases `dulce_salado_qa_%` devolvió cero filas.

Las peticiones a `wa.me` se interceptan dentro de Playwright: se comprueba URL/texto completo sin enviar un mensaje. La salida no elimina el carrito. CI repite Django, Ruff, migraciones, Node y navegador, y conserva capturas como artifact. El estado de los runs publicados se registra en `EXECUTION_STATUS.md`.

## Validación manual pendiente del dueño

1. Configurar el WhatsApp real y cargar categorías/productos/precios comerciales reales.
2. Probar en Android/iOS real, con teclado virtual y TalkBack/VoiceOver; verificar lectura, foco y retorno desde WhatsApp.
3. Verificar que el número pertenece al comercio y que WhatsApp móvil/web precarga el mensaje. Para texto largo, probar copiar el mensaje completo.
4. Validar nombre/colores con el logo original cuando esté disponible.

Estas comprobaciones comerciales/dispositivo real no se sustituyen por axe ni por simulación de anchura. Despliegue, TLS y backups de producción están fuera del MVP. No hay cuentas de clientes ni persistencia de pedidos.
