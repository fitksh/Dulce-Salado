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
| Sin pedidos/stock | Category/Product, configuración comercial e intervalos; carrito local y cálculos stateless sin modelos de pedidos |

## Aislamiento y CI

El servidor `tests/browser_server.py` crea una base PostgreSQL con nombre `dulce_salado_qa_<aleatorio>` y media temporal. Los productos, precios, administrador y teléfono son fixtures descartables de test. La base comercial se comprobó vacía (0 productos, 0 categorías). Tras detener el contenedor QA, la consulta de bases `dulce_salado_qa_%` devolvió cero filas.

Las peticiones a `wa.me` se interceptan dentro de Playwright: se comprueba URL/texto completo sin enviar un mensaje. La salida no elimina el carrito. CI repite Django, Ruff, migraciones, Node y navegador, y conserva capturas como artifact. El estado de los runs publicados se registra en `EXECUTION_STATUS.md`.

CI ampliada verificada con resultado success para el commit `abc3727`, [run 38086302160](https://github.com/fitksh/Dulce-Salado/actions/runs/38086302160), incluidos tests de navegador y guardado de capturas.

## Validación manual pendiente del dueño

1. Configurar el WhatsApp real y cargar categorías/productos/precios comerciales reales.
2. Probar en Android/iOS real, con teclado virtual y TalkBack/VoiceOver; verificar lectura, foco y retorno desde WhatsApp.
3. Verificar que el número pertenece al comercio y que WhatsApp móvil/web precarga el mensaje. Para texto largo, probar copiar el mensaje completo.
4. Validar presentación del logo provisto y datos comerciales configurados.

Estas comprobaciones comerciales/dispositivo real no se sustituyen por axe ni por simulación de anchura. Despliegue, TLS y backups de producción están fuera del MVP. No hay cuentas de clientes ni persistencia de pedidos.

## Etapa complementaria UX/UI — QA final

Historial MVP anterior conservado. Verificaciones actuales: 60 tests Django, 7 Node y 16 comprobaciones Chromium (15 escenarios), check/Ruff OK y makemigrations sin cambios. PostgreSQL y Python 3.12/Django 5.2.18 en Docker; migraciones 0003 BusinessSettings y 0004 OpeningInterval aplicadas. Ninguna dependencia nueva de runtime.

| Mejora | Evidencia ejecutada |
| --- | --- |
| Logo/header/Instagram | WebP 150×150 de fuente provista; enlaces accesibles, header en una fila y sin overflow a 360/390/430/1280 px |
| Búsqueda y categorías | Orden nombre/marca/descripción, filtros/paginación Django; formulario GET móvil con búsqueda conservada también sin JS |
| Cantidades/condiciones/placeholder | Botones 44×44, decimales exactos, mínimo e inválidos; mismo comportamiento en catálogo/carrito; condición específica conservada |
| Feedback y Admin | Éxito verde con Ver carrito/contador, axe tras agregar; creación/edición de productos/categorías con un mensaje nativo de éxito |
| Scroll/concurrencia | Carrito de 12 artículos, edición por debajo de 2000 px; mismo input y foco, diferencia de scroll menor de 3 px durante/después; teclado, respuestas fuera de orden y recuperación de red con controles visibles/importes ocultos |
| CSV | Permisos, 111 productos filtrados incluyendo página no visible, búsqueda/filtros, BOM, ;, coma decimal, comillas/saltos de línea y protección de fórmulas; descarga real filtrada en navegador |
| Cómo llegar | Ausencia de dirección sin enlace, singleton/permiso Admin, URL codificada/exacta validada, navegación Maps interceptada y capturas de las cuatro anchuras |
| Horarios | Configuración inédita/borrador neutra, semana vacía explícitamente cerrada, 2/3 intervalos, límites, zona Buenos Aires, superposiciones y cambios/borrados en Admin; details con teclado/sin JS; reloj simulado pasa de cerrado a abierto sin fetch periódico |
| Regresión MVP | Precios/tarifa manual, localStorage, cambios de unidad/producto, sincronización, diálogo/aviso completo, revalidación, cancelación y WhatsApp interceptado sin envío |

Cero infracciones axe WCAG A/AA en catálogo, confirmación de agregado, carrito/revisión/vacío, Cómo llegar y desplegable horario. Las listas de avisos mantienen su semántica. El reloj anuncia sólo cambios de estado. Las fixtures comerciales de QA viven exclusivamente en la base/media descartables.

CI de tareas 1–6 success: runs 38093591790, 38093785080, 38094129519, 38094267809, 38094437168 y 38094790574. CI del cierre se registra tras publicar en EXECUTION_STATUS; no se presume su resultado.

QA final publicada y CI success verificada: commit `61d5e52`, [run 38095362239](https://github.com/fitksh/Dulce-Salado/actions/runs/38095362239). Regresión también confirma retorno de foco después de cerrar el diálogo con Escape. Entorno local reconstruido, HTTP 200 en las tres vistas públicas, migraciones al día y sin bases QA restantes.

Un run posterior (38095501842) detectó una comprobación prematura de foco tras Escape. Se corrigió el foco explícito en close y se espera el recálculo antes de comprobarlo. Corrección verificada localmente y en [CI success run 38095823292](https://github.com/fitksh/Dulce-Salado/actions/runs/38095823292), commit `95e7926`: las 60 pruebas Django, 7 Node y 16 Chromium completas pasan. No quedan fallos conocidos de implementación/QA automatizado.

Pendientes manuales del dueño: revisar dirección/enlace Maps, horario semanal y WhatsApp/catálogo reales. La instalación local ya tiene dirección y enlace exacto, 12 intervalos publicados y teléfono configurado; esta comprobación confirma presencia, no su exactitud comercial. En nuevas instalaciones cargar esos datos desde Admin/entorno. En teléfono Android/iOS probar teclado virtual, −/+, retorno de Maps/WhatsApp y lector TalkBack/VoiceOver. Abrir CSV en su Excel es-AR y revisar acentos, columnas, decimales y textos protegidos. Confirmar reloj del dispositivo; no hay feriados/excepciones.

## Segunda iteración UX/UI — QA

Historial de las etapas anteriores conservado. Verificación completa local: 63 pruebas Django, 7 Node y 22 comprobaciones Chromium (21 escenarios), check/Ruff correctos y makemigrations sin cambios. Sin nuevas dependencias o migraciones.

| Ajuste | Evidencia |
| --- | --- |
| Header/horarios | Dentro de header, altura menor a 150 px, apertura no mueve main; cinco anchuras, siete días, intervalos/estado/zona intactos, cierre control/exterior/Escape y foco, fallback sin JS |
| Catálogo/filtros | Textos retirados, h1 Nuestros productos, etiqueta oculta/placeholder; cambio automático conserva q/categoría/URL; GET sin JS conserva botón; búsqueda/paginación Django siguen correctas |
| Footer/toolbar | Icono ubicación, centrado móvil, Instagram oficial abre otro contexto con opener null/referrer vacío; toolbar móvil igual ancho/alineación de tarjetas |
| Maps | URL iframe fija exacta, title/lazy/referrerpolicy/allowfullscreen, cinco anchuras y altura responsive; recurso interceptado o bloqueado; dirección/link Admin y navegación externa conservados |
| Fotos/condiciones | Un dialog reutilizable, mismo archivo/contain, botón/Escape/fondo y retorno de foco; sin foto no amplía; condición específica rosa suave sólo con mayorista seleccionado en carrito |
| Avisos | Éxito con Ver carrito tras scroll >2000 px, sin cambiar foco/scroll; errores de tarifa/cantidad/red/storage, un aviso live visible, reemplazo, 5/8 segundos, pausa de 10 s con foco y cierre teclado; errores persistentes bloquean total/revisión tras ocultación del aviso |
| WhatsApp | Contexto nuevo con opener null/referrer vacío; pestaña y storage intactos; fallback ante popup bloqueado abre enlace seguro; precios cambiados/cancelación/error/red/cambio en otra pestaña cierran provisional sin navegar; copia con éxito y fallback selecciona texto completo |
| Regresión | Django Admin/permisos/CSV, búsqueda, precisión de importes, tarifas manuales, storage/sincronización, productos/unidades/precios cambiados, concurrencia/scroll, aviso obligatorio y mensaje completo |

Responsive comprobado a 360, 390, 430, 768 y 1280 px. Axe WCAG A/AA sin infracciones en estados inspeccionados (catálogo, foto, avisos, carrito/revisión/vacío, Maps y horarios). QA usa exclusivamente base/media descartables; Google Maps, Instagram y WhatsApp interceptados. No se hicieron envíos reales. Capturas finales se inspeccionan antes de publicar; la CI final se registra en EXECUTION_STATUS.

Pendientes manuales: Android/iOS con teclado real, TalkBack/VoiceOver, retorno de WhatsApp/Instagram/Maps y comportamiento de bloqueadores; verificar pertenencia del teléfono/datos comerciales e iframe real. Si cambia ubicación, actualizar tanto Admin como URL fija en templates/directions.html. Configuración existente conservada. Excel es-AR y feriados/excepciones siguen con los límites ya documentados. No hay bloqueo de implementación ni infraestructura nueva.

Capturas finales inspeccionadas y entorno Docker reconstruido; migrate sin pendientes/check OK, HTTP 200 en tres vistas públicas. Servidor/base QA descartados (consulta sin filas). Configuración comercial real preservada, verificando únicamente presencia: dirección/enlace, 12 intervalos publicados y teléfono configurado. La exactitud comercial y carga externa Maps se validan manualmente.

Segunda iteración publicada y CI completa success: a43a578, [run 38101095717](https://github.com/fitksh/Dulce-Salado/actions/runs/38101095717). Las 63 Django, 7 Node y 22 Chromium, checks/lint/control de migraciones pasan también en CI. No quedan correcciones de implementación pendientes. Cierre documental posterior registra este resultado funcional; su hash/run se verifica al publicarlo.

Regresión adicional: tocar dentro del iframe Maps también cierra horarios, conservando el foco en el mapa. El clic del iframe no burbujea al padre; el cierre detecta el foco IFRAME tras blur. Reproducido antes/después en lectura local y cubierto dentro del escenario horario Chromium. 6 Django afectados, 7 Node y 22 Chromium OK, checks/lint/migraciones correctos. Sin cambios de cálculo/configuración; la CI propia de este ajuste se consulta tras publicar.
