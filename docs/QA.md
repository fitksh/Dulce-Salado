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

## Correcciones puntuales — imágenes

Recorte reproducido mediante fotos QA con bordes en tres proporciones: en 1280 el marco medía 210 px y el enlace vertical 716 px. Fila automática Grid y altura porcentual del enlace permitían crecimiento intrínseco; overflow recortaba. Encaje Flex definido: marco/enlace/imagen 210 px, contain centrado. Tests geométricos y capturas photo-{anchura}-{1..3}.png en 360/390/430/768/1280 confirman cuatro bordes completos. Dialog sin encabezados/texto comercial visible, descripción oculta y × accesible 44 px; Escape/fondo/foco/enlace sin JS. 10 Django y 22 Chromium OK, Ruff y axe OK. Historial previo conservado; el recorte no estaba detectado por la fixture horizontal uniforme anterior.

Header corregido: tres regiones alineadas en fila desde 800 px; en 360/390/430/768 columna con marca, horarios y carrito centrados y controles ≥44 px. Tests comparan centros, separación y límites; apertura no cambia main ni desborda viewport. Panel abierto, siete días, reloj sin peticiones, cierre exterior/Escape/iframe y fallback sin JS conservados. 16 Django, 7 Node, 22 Chromium/check OK; axe y capturas inspeccionadas. Altura compacta verificada <200 px móvil y <120 px escritorio (sustituye criterio de la iteración anterior).

Cómo llegar unificada: h1 Dirección dentro de región única, address/botón Admin y mismo iframe anidado. Tests geométricos verifican columnas a 1280 y pila a 360/390/430/768, mapa dentro de región y sin overflow; clic en iframe QA y navegación Maps interceptada. Ausencia de dirección no ofrece enlace. 16 Django, 22 Chromium y Ruff OK; axe en cinco anchuras y capturas directions inspeccionadas. URL y políticas exactas preservadas; Maps real se comprueba al actualizar entorno local.

Footer centrado en todas las pantallas: text-align y justify-content center base; grupo de enlaces centrado geométricamente, dos iconos y objetivos ≥44 px. Destinos originales/Instagram en nueva pestaña conservados. 10 Django y 22 Chromium OK, axe sin infracciones; las cinco capturas footer inspeccionadas.

## Correcciones puntuales — QA final

Suite completa ejecutada: 63 Django, 7 Node y 22 Chromium correctos; check/Ruff OK y makemigrations sin cambios. Las cuatro áreas tienen pruebas actualizadas. Regresión completa de precios, CSV/Admin, almacenamiento, concurrencia, revisión/revalidación y WhatsApp pasa sin alterar su implementación.

| Área | Comprobación |
| --- | --- |
| Miniaturas | Tres proporciones con bordes/esquinas visibles y geometría marco/enlace/imagen 210 px en cinco anchuras; contain centrado sin distorsión |
| Modal | Tres proporciones en cinco anchuras; 15 capturas expanded; sólo foto/×, etiquetas ocultas, teclado/exterior/foco y enlace nativo sin JS |
| Header | Centros/separaciones en tres regiones desde 800; columna centrada bajo 800; cinco anchuras más límite 800, controles ≥44 px |
| Horarios | Main inmóvil al abrir, panel dentro del viewport; siete días/reloj/cierres/control/Escape/iframe/sin JS conservados; axe en cada ancho |
| Dirección | Región única con h1 Dirección, sin título superior; dos columnas/una columna, mapa útil dentro del contenedor; URL/title/lazy/seguridad exactos |
| Footer | Enlaces/iconos y párrafos centrados a todas las anchuras, dos SVG y enlaces ≥44 px; destinos/pestaña Instagram conservados |

Capturas QA inspeccionadas de fotos/modal, catálogo, horarios, dirección y footer. Adicionalmente capturas live-* del entorno comercial sólo en lectura: fotografías verticales reales completas, cinco anchuras sin overflow/axe del catálogo sin infracciones, header 165/183/93 px y main inmóvil. Datos existentes preservados. Google Maps real cargó HTTP 200 y se ve en capturas móvil/escritorio al permitir la lectura de red bloqueada inicialmente por sandbox. QA automático intercepta destinos externos para no enviar mensajes ni depender de esos servicios.

Entorno local actualizado, tres páginas públicas HTTP 200, servidor/base QA eliminados (consulta sin filas). CI de tareas 1–4 success: 38104627303, 38104718180, 38104812406 y 38104891571. CI final se registra después de publicar. Pendientes manuales habituales: teléfono Android/iOS, lector TalkBack/VoiceOver, retorno de aplicaciones externas y exactitud comercial. Sin cambios de datos/modelos/dependencias/migraciones ni reglas.

QA final publicada con CI completa success: `69902fb`, [run 38105183767](https://github.com/fitksh/Dulce-Salado/actions/runs/38105183767). Las 63 Django, 7 Node y 22 Chromium, check/Ruff/control de migraciones pasan también en CI. Iteración completada; cierre documental posterior registra este resultado y se verifica al publicar. No quedan correcciones de implementación pendientes. Capturas reales comerciales y mapa cargado inspeccionados a cinco anchuras; datos preservados.

Regresión final de orientación horizontal: modal a 844×300/390, sin scroll ni parte de la imagen fuera del dialog. Se reserva altura para cierre/padding dentro de 90dvh. Fallo geométrico previo reproducido (foto y=297, borde y=285), corrección verificada y capturas image-landscape-300/390 inspeccionadas; fotografía real vertical también cabe completa. 10 Django afectados, 7 Node, 22 Chromium/check/Ruff/migraciones OK. El cierre documental 144e079 tuvo CI success run 38105345534. CI propia del ajuste se consulta tras publicar; no quedan pendientes de implementación.

## Nueva iteración UX/UI y demos — 2026-10-11

Suite completa: 78 Django, 7 Node y 24 comprobaciones Chromium (23 escenarios) correctas; check/Ruff sin incidencias y makemigrations sin cambios. Axe WCAG A/AA sin infracciones en los estados revisados. Cinco anchuras 360/390/430/768/1280 y límite 800 px. La suite mantiene todas las regresiones de precios/decimales, CSV/Admin, controles/foco/scroll, almacenamiento, horarios, copia y WhatsApp.

| Área | Evidencia nueva |
| --- | --- |
| Header/horarios | Logo 64 px, Catálogo/Carrito iguales y juntos, aria-current, tres regiones, controles ≥44 px, seis bordes entre días, reloj/cierres sin cambios |
| Ubicación | URL principal nueva, 301 anterior, info centrada, Admin intacto, mismo iframe y políticas; cinco anchuras/axe y mapa real visible en lectura |
| Carrito | Título oculto, sin toolbar, foto actual 56 px contain y visor compartido; apertura tras recálculo, Escape/cierre/foco, cinco anchuras/nombre largo, imagen eliminada en QA no deja placeholder/columna |
| Almacenamiento | Corrupto conserva dato hasta clic Restablecer, no borra otras claves; JSON null/esquemas inválidos/duplicados identificados; bloqueo de lectura/escritura informa y no ofrece restablecimiento ni revisión |
| Catálogo | 45 fixtures explícitos en Admin de base descartable, cuatro páginas 12/12/12/9, 45 IDs distintos, rangos, Anterior/Siguiente y q; 15 por categoría en dos páginas 12/3, categoría y q conservados; GET sin JS, páginas inválidas/vacío/única en Django |
| Revisión | Título oculto mantiene foco/nombre; aviso íntegro y textarea/copia/cancelación/fallback/validación externa probados sin envíos |
| Seed | 10 tests de comando explícitos con base/media temporales: 45/15, datos válidos, simulación, DEBUG, idempotencia/ediciones, categorías ambiguas, rollback y limpieza por procedencia, archivos perdidos/corruptos y PK reutilizada |

Capturas inspeccionadas: catálogo comercial a las cinco anchuras, carrito móvil/escritorio/nombre largo, revisión, horarios/tablet, ubicación móvil/escritorio con mapa real, catálogo demo y paginación en cinco anchuras. Chromium no ejecuta el seed como fixture: lee el dataset estático y crea sus productos explícitamente mediante Admin aislado.

Entorno Docker reconstruido conservando volúmenes/.env. Tres páginas principales HTTP 200 y ruta anterior 301. Base comercial: 6 productos, 3 categorías, 12 intervalos; huella de todos los registros iguales antes/después de actualizar y de las comprobaciones en lectura. El seed no se ejecutó allí y no existe manifiesto comercial. QA detenido, consulta de bases QA sin filas. CI de las seis tareas funcionales success; CI ampliada se registra al publicar en EXECUTION_STATUS.

Próximo paso manual: Ctrl+F5, teléfono Android/iOS y lector; cargar dirección completa desde Admin, verificar datos y abrir/retornar de aplicaciones externas. Seed opcional sólo mediante instrucciones README y DEBUG; conservar manifiesto para limpieza, demos editados requieren revisión manual. No hay cambios de modelos, dependencias, migraciones ni reglas comerciales.

## Exportación PDF y ajustes puntuales — QA 2026-10-11

88 tests Django, 7 Node y 25 comprobaciones Chromium correctos. check/Ruff OK y makemigrations sin cambios. Docker actualizado con Django 5.2.18, Pillow 12.3.0 y ReportLab 5.0.1. Poppler instalado exclusivamente para inspección QA local/CI; no forma parte del Dockerfile ni de la ejecución del sitio.

| Área | Evidencia |
| --- | --- |
| Header | 320/360/390/430/768/800/1280: tres enlaces en una fila, logo 64, objetivos ≥44, aria-current, regiones sin overflow; horarios/reloj/cierres sin cambios |
| PDF Admin | Anónimo/no staff redirigidos, staff sin permisos 403, view/change permitidos; GET y POST/PUT 405; attachment application/pdf válido, filtros inválidos 400, botones mantienen parámetros |
| Datos/orden | Search nombre/marca, categoría/unidad/activo, orden descendente y página no visible: 111 registros exactamente en orden de CSV/ChangeList; incluye inactivos y [DEMO] cuando corresponde |
| Documento | A4, Unicode/accentos/ñ, ARS y campos opcionales, estado inactivo, pie numerado/nota comercial; vacío con mensaje explícito, 180 letras sin espacios y descripción de 300 repeticiones completos |
| Fotos PDF | Sólo variante con fotos, horizontal/vertical/cuadrada en dimensiones proporcionales hasta 240 px; imágenes uniformes distintas no colisionan; original sin modificar; ausente/faltante/corrupta no aborta |
| Paginación | Registros normales permanecen juntos, descripción mayor que la hoja se divide sin truncar; encabezado/pie por página. La comprobación de texto descarta el marco repetido antes de verificar continuidad |
| Papelera | SVG inline decorativo, aria-label contextual y fallback, área 44×44; Enter elimina sólo el elegido, restante/storage/contador/aviso y accesibilidad conservados |
| Carrito | Bajo 800 foto 56 px y composición móvil; desde 800 foto 132 y todos los campos a la derecha, sin foto no hay hueco; nombre largo, imagen quitada en Admin, visor tras recálculo |
| Regresión | Misma identidad del input/foco y scroll (<3 px de diferencia) durante/después de recálculo en móvil y escritorio; respuestas fuera de orden/red/storage, tarifas manuales, precios actuales, revisión/WhatsApp, CSV y Admin correctos |

Dos PDFs ficticios generados por tests/pdf_examples.py sin consultas ni escrituras de base: .qa/pdfs/catalogo-con-imagenes.pdf (55.191 bytes) y catalogo-sin-imagenes.pdf (45.447 bytes), tres páginas cada uno. Renderizados a PNG con pdftoppm; las seis páginas finales inspeccionadas: fotos completas/proporcionales, etiquetas sin solapar, texto legible y márgenes/separadores/pie correctos. Las fotos/archivos de estos ejemplos sólo viven en media temporal/.qa ignorada; el servicio de exportación no guarda PDFs.

Capturas inspeccionadas de carrito 320/800/1280, nombre largo 800/1280, sin foto 1280 y foco/scroll desktop. Lectura del entorno comercial: header en seis anchuras y carrito con fotografía vertical real en siete (incluida 640 como espacio reducido), axe WCAG A/AA sin infracciones; capturas live-pdf-* 320/800/1280 revisadas. Zoom nativo a 200% permanece como comprobación manual: reducir viewport no sustituye probar el control de zoom real del navegador.

Actualización Docker y consultas/recálculos públicos en contexto de navegador descartable mantienen idénticas las huellas de TODOS los registros comerciales y archivos de fotos, comprobadas antes/después: 51 productos existentes, 3 categorías, 1 configuración y 12 intervalos. No se ejecutó seed en la base comercial. GET /, /carrito/ y /ubicacion/ HTTP 200; QA detenida y consulta de bases QA sin filas. Cambios locales anteriores del propietario (panel horarios 260 px y rango sin Mostrando) se conservan y excluyen de commits.

Pruebas manuales concretas: entrar a Admin, aplicar filtros/orden y descargar ambos PDFs; comparar con CSV y revisar vista previa A4/visor/impresora propios. Probar nombres/descripciones comerciales y tiempos con un catálogo más grande. En móvil real/lector, papelera por teclado/voz y visor; en escritorio, zoom 200%, cantidad/tarifa/foco/scroll. No se ha hecho impresión física ni envío de WhatsApp. No hay modelos/migraciones/reglas/infraestructura nuevas; sólo la dependencia PDF directa autorizada. Resultados CI de las tareas y cierre en EXECUTION_STATUS.

QA final publicada: 4df24c2, [CI success 38154032727](https://github.com/fitksh/Dulce-Salado/actions/runs/38154032727). Los mismos checks y suites completos pasan en CI. Las cuatro tareas anteriores también tienen CI success; detalle en EXECUTION_STATUS. Iteración completa, entorno local listo, sin correcciones de implementación pendientes.

## Nuevas exportaciones PDF, imágenes e importación CSV

Tarea 1: 17 PDF/CSV, 25 Chromium, check/Ruff/migraciones correctos. Tabla compacta A4 horizontal sin categoría/fotos, siete columnas, ARS/Unicode, inactivos y campos opcionales; 111 registros filtrados en orden idéntico a CSV/ChangeList. GET/permisos y botones conservan filtros. Nombres de 180 caracteres, descripción de 300 repeticiones y condiciones extensas sin truncar; filas normales juntas, encabezados/pies por página. Ejemplo ficticio de seis páginas renderizado e inspeccionado completo. Las listas anteriores conservan los ejemplos de 55.191/45.447 bytes y sus tests. Descargas reales de las tres variantes PDF correctas en navegador aislado. Datos comerciales no usados para importaciones ni fixtures.

Tarea 2: 19 PDF/CSV y 25 Chromium correctos. Misma cobertura funcional aplicada a las dos tablas; fotos horizontales/verticales/cuadradas completas, inline JPEG distintos sin colisión, archivos originales intactos. Ausente/faltante/corrupta no aborta; la compacta no incluye fotos/avisos. Los ocho encabezados completos se conservan en la variante con imágenes. Siete páginas ficticias inspeccionadas, fotos de unos 51 px y columnas de 9 pt legibles. Los cuatro formatos se descargan mediante los botones reales del Admin, con filtros/nombres correctos. Ejemplos de listas idénticos y tablas de 48.642/59.659 bytes.

Tarea 3: 24 Django y 25 Chromium correctos, axe sin infracciones. Marcos cuadrados uniformes incluso placeholders, cover proporcional y centrado sólo en catálogo; visor/carrito contain. Capturas reales de 360/390/430/768/1280 inspeccionadas, más ocho fotos existentes en escritorio y sus visores completos. Fixture de envase con etiqueta al borde muestra el recorte deliberado y su recuperación al ampliar. Fotos comerciales centrales conservan identificación; cover recorta fondo y algo del extremo del envase, por lo que se recomiendan fuentes cuadradas. No se añadieron excepciones por producto: no hay inferencia de contenido visual. Las huellas de TODOS los registros/fotos comerciales permanecen idénticas a la inicial (52 productos). No se ejecutó seed ni se regeneró media.

Tarea 4: 19 tests de motor/importación y exportación CSV, check/Ruff/migraciones correctos. Cobertura: UTF-8 con/sin BOM, ;/coma exactos, comillas/separadores/multilínea y fila física, defaults/valores opcionales, decimales/cero/mayorista mayor admitido, kg 0.05 y pasos enteros. Faltantes/categorías ambiguas/unidades/precios inválidos, límites de modelo, filas/tamaño/encabezados/archivo malformado/binario y HTML/fórmulas rechazados. Duplicados normalizados reales/demo/intraarchivo omitidos, discrepancias intraarchivo bloquean lote; previews sin escrituras, cambio de contenido/categoría/duplicado exige revisar, segundo guardado fallido revierte primero. Reejecución/exportación compatible sin sobrescribir ni crear duplicados. Sólo bases aisladas; UI y permisos se validan en tarea 5.

Tarea 5: 49 CSV/PDF y 26 Chromium correctos, check/Ruff/migraciones. Autenticación/staff/add obligatorio, sólo lectura/cambio denegados, GET/POST/otros métodos y CSRF en análisis/confirmación. Plantilla ficticia BOM y 10 columnas exactas, sin escrituras. Preview y selección sin crear; confirmación explícita, payload alterado/vencido/de otro usuario o sin permisos rechazado, replay sin duplicar, cambios de duplicados/categorías exigen nueva revisión y errores visibles por fila. Transacción fallida revierte todo y muestra error. Lote Unicode cercano al límite conserva las 30 filas/textos completos y cabe en firma/POST. No datos masivos en sesión ni imágenes importadas.

Capturas Admin preview/error 390 y preview 1280 inspeccionadas: tabla desplazable propia sin overflow de página, encabezados espaciados, foco/ArrowRight, botones nativos y enlaces subrayados; axe sin infracciones. Chromium selecciona CSV, analiza y verifica ausencia del nuevo mediante otra pestaña, confirma, comprueba resumen/alta inactiva/paso 0.05/precio/duplicado omitido. HTML inválido queda escapado, sin nodos ejecutables ni confirmación. Documentación/plantilla versionadas y descarga autenticada disponibles; no se importó ningún lote en la base comercial.

### QA completa de la nueva iteración

126 Django, 7 Node y 26 Chromium ejecutados completos y correctos sobre PostgreSQL/bases aisladas. Poppler disponible, sin omisiones PDF; check/Ruff y makemigrations --check --dry-run correctos. Nuevo test con dos conexiones y confirmaciones concurrentes demuestra una sola creación y una nueva vista previa para la otra. Integración CSV/carrito: paso explícito 0.05 kg admite 0.25 y calcula $ 3.625,00 sobre minorista $ 14.500,00; 0.26 se rechaza, sin cambiar el carrito.

Cuatro PDFs de ejemplo regenerados con modelos sin guardar/media temporal: listas 3+3 páginas (55.191/45.447 bytes), tablas 6+7 páginas (48.642/59.659 bytes). Las 19 PNG finales, bajo .qa/pdfs/final-*, se revisaron íntegramente. Unicode/ARS correctos, todas las cabeceras/pies y columnas conservados, texto extenso completo con continuación, sin solapamientos. Las miniaturas PDF muestran los cuatro bordes en sus proporciones originales; ausente/faltante/corrupta se indican sin abortar. La lectura de texto respeta los saltos de línea propios de las columnas.

Capturas comerciales live-final-catalog-* de viewport en 360/390/430/768/1280 revisadas realmente, además de las ocho fotos/visores de la tarea 3: marcos y placeholders cuadrados, cover centrado sin deformación ni overflow. La identificación comercial central permanece visible; una etiqueta extrema de prueba se recorta en tarjeta y se recupera completa en el visor contain. Recomendación: preparar fuentes cuadradas, sin modificar originales ni agregar heurísticas.

Docker local actualizado sin cambiar .env/volúmenes. Todos los registros y fotos comerciales con huellas idénticas a la inicial; 52 productos, 3 categorías, 1 configuración y 12 intervalos. No se importó ni se ejecutó seed allí. HTTP 200 en las tres páginas públicas. QA detenida y ninguna base QA restante; dos cambios locales previos del dueño conservados fuera de commits. Resultados de publicación/CI en EXECUTION_STATUS.

Pruebas locales siguientes: Ctrl+F5; Admin → Productos → filtros/búsqueda/orden → PDF tabla compacta y PDF tabla con imágenes, comparar conjunto con CSV y revisar A4 horizontal. Para CSV, descargar plantilla, reemplazar categoría/filas ficticias, preparar UTF-8 y precios sin miles, analizar/revisar/corregir, confirmar explícitamente y comprobar creados/omitidos; fotos después desde cada producto. Límites: 256 KiB/500 filas, 4000 caracteres por campo con límites menores del modelo, firma por usuario de 15 minutos/2 MiB, sólo altas. Excel/Sheets propios, impresión física, teléfono/lector y zoom nativo 200% quedan como pruebas manuales; no se enviaron mensajes de WhatsApp.

## Ajustes puntuales de imágenes, catálogo, carrito y PDF

Tarea 1: 33 Django, check/Ruff y 26 Chromium correctos. Geometría real de tres proporciones en 360×800, 390×844, 430×932, 844×300, 1280×800 y 1440×900, además de 768: margen entre imagen y borde 11 px (10 de padding + 1 de borde), proporción natural exacta, sin scroll ni ampliación superior al original, cierre ≥44×44. Las 18 capturas viewer-* solicitadas se inspeccionaron realmente; no hay bandas blancas desproporcionadas ni recortes, incluso con 300 px de altura. Cierres/Escape/fondo, restauración del foco, visor compartido en carrito, fallback sin JS y axe correctos. CSS suficiente; no cambios de JS/templates/fotos.

Tarea 2: 13 Django y 26 Chromium correctos, Ruff OK. Número real de tarjetas en primera fila: 1 en 320/360/390/430, 2 en 768/800, 3 en 1000 y 4 en 1280/1440. Mismo ancho/alineación, controles sin desbordar y objetivos ≥44. Capturas de grilla 390/768/1000/1280 inspeccionadas, sin scroll horizontal. Nombre de 180 letras, marca de 100, descripción y condición extensas en DOM aislado inspeccionados a 390/1280; marca sin espacios ahora envuelve exclusivamente dentro del catálogo. Fotos cuadradas/cover, placeholder, paginación de 12 y acciones intactos. La inspección adicional en contexto comercial de lectura confirma scrollWidth de marca igual a clientWidth después del ajuste.

Tarea 3: 11 Django, 5 Node y 26 Chromium correctos, Ruff OK. Fotos de 132 px centradas dentro de la tarjeta desde 800, diferencia entre centros <1 px; controles a la derecha sin superposición. Capturas de condición extensa/horizontal 1280, nombre largo/cuadrada 800/1280, vertical 800/1280 y móvil 390 inspeccionadas. Cambio real de cantidad 0.3→0.4 y de mayorista→minorista produce $36,20/$40,10, mantiene foco/scroll (<3 px) y foto centrada; después se restablece el fixture. Regresión de tres proporciones en carrito largo y visor/foco correcta. Sin foto no reserva columna; caso inspeccionado a 1280. Móvil de 56 px sin cambios CSS/DOM. Fixture extendido sólo en servidor/base QA; datos comerciales intactos.

Tarea 4: 23 PDF/CSV y 26 Chromium completos correctos, check/Ruff/migraciones OK. Logo de 16 mm completo/proporcional y nombre a la derecha en todas las páginas de las cuatro variantes; recurso ausente/corrupto conserva el encabezado textual y una descarga válida. XML verifica posición/tamaño/logo repetido, etiquetas bold con valores normales y markup comercial literal escapado. El recuento sin imágenes refiere ahora sólo a fotografías inline, excluyendo el logo compartido.

Foto de lista centrada respecto de todo el bloque visible (<6 px), texto TOP, descripción normal. Regresión con 300 repeticiones y fotografía: más de dos páginas, todas las palabras, una única foto y sin duplicados. ReportLab MIDDLE acumulaba padding en una fila enorme y bloqueaba el test anterior: dividir en TOP y centrar después cada fragmento resuelve el problema sin cambiar las tablas. Todas las suites PDF pasaron tras la corrección; no se oculta ni se omite la prueba extensa.

Ejemplos exclusivamente ficticios/modelos sin guardar/media temporal: listas 3+3 y tablas 6+7 páginas, 91.867/82.098/85.563/96.728 bytes. Las 19 PNG regeneradas e inspeccionadas completas muestran encabezados sin solapamiento, etiquetas legibles, fotos completas/centradas, ARS/Unicode y continuaciones sin truncar. Separadores/márgenes/pies conservados; columnas, abreviaturas y distribución de ambas tablas intactos salvo logo/nombre del encabezado. Sin modificaciones de modelos, migraciones, dependencias, fotografías o CSV. Browser verifica descarga de los cuatro formatos filtrados y conserva sus regresiones de negocio/accesibilidad. QA detenida tras 26/26.

### QA final de los ajustes visuales

130 tests Django completos sobre PostgreSQL, 7 Node y las 26 pruebas Chromium de la implementación final correctos. Sin omisiones PDF; check/Ruff y makemigrations --check --dry-run correctos. No hubo cambios de código después de esas suites. Las 19 páginas finales y capturas de visor/carrito/grilla se inspeccionaron realmente; visor vertical/cuadrado/horizontal en 360×800, 390×844, 430×932, 844×300, 1280×800 y 1440×900. Grilla de cuatro columnas/controles completos a 1280/1440, dos en tablet y tres a 1000, sin overflow. Foco/scroll y tarifas/cálculos anteriores sin regresiones.

Catálogo comercial en 360/390/430/768/1280, ocho fotografías existentes en visor desktop y vertical móvil regenerados/revisados sólo en lectura. Fotos completas con marco mínimo, sin ampliación indebida ni deformación. Huellas finales de TODOS los registros y bytes de fotografías idénticas a la inicial: 52 productos, 3 categorías, 1 configuración y 12 intervalos. Ningún seed/import en esa base; GET /, /carrito/ y /ubicacion/ HTTP 200. QA detenida y ninguna base QA restante. El servidor Docker utiliza el código actual por bind mount; configuración/volúmenes/dependencias intactos.

Archivos de aplicación de esta iteración: static/css/site.css y catalog/pdf.py. Tests: catalog/test_pdf.py, tests/browser.spec.cjs y tests/browser_server.py (sólo fixture de condición extensa). Seguimiento: README, UX_UI, ARCHITECTURE, ROADMAP, EXECUTION_STATUS y QA. Sin cambios en models/migraciones, Admin/CSV, JS/templates de producto ni fotos. Las dos ediciones locales previas del propietario se mantienen fuera de commits.

Prueba local concreta en README: Ctrl+F5, catálogo 1280/fotografías, carrito desde 800/cantidad/tarifa, Admin → Productos → filtros/orden → cuatro PDF. Visor/impresora propios, zoom nativo 200% y teléfono/lector son comprobaciones manuales pendientes; no se envió WhatsApp. Estado de publicación/CI registrado en EXECUTION_STATUS, sin anticipar trabajo futuro.

Publicación final de QA: 3a6f97a, [CI success 38173168024](https://github.com/fitksh/Dulce-Salado/actions/runs/38173168024). Las cinco tareas y sus suites completas pasan en CI; roadmap completo. El commit de cierre sólo registra estos resultados y no cambia la implementación verificada.

## Copiado y formato de WhatsApp

19 tests Django afectados (WhatsApp/carrito) y 149 completos correctos en Docker/PostgreSQL; check/Ruff/makemigrations correctos. 7 Node y 35 Chromium completos correctos, sin omisiones. Tras mejorar sólo el tamaño de capturas, se repitieron las nueve comprobaciones de copiado correctamente; ningún cambio de implementación posterior a las suites completas.

Formato: comparación exacta de un producto con marca/mayorista/0,3 kg, varios productos en orden con minorista/unidad y mayorista/paquete, marca vacía/espacios omitida, ARS y cantidades/subtotales/total actuales. Títulos/subtotales/total con un par de asteriscos, divisor y líneas en blanco, advertencia/cierre exactos. 100 productos con nombres largos/accentos sin truncamiento. Marcadores especiales y saltos en nombres/marcas neutralizados sólo en presentación; valores originales comprobados sin cambios. Vista previa y enlace revalidado igualan exactamente whatsapp_message y el parámetro text decodificado; el navegador también compara su textarea con la salida y enlace alternativo.

Copiado: Clipboard API real con permisos QA, API ausente y fallback confirmado en el mismo callback del clic, rechazo moderno con fallback, retorno false/excepción/método ausente y selección manual sin éxito falso. Un solo textarea/aviso, foco/selección/scroll previos restaurados al copiar; modal y localStorage intactos. Clics repetidos mientras hay promesa producen una sola operación/aviso; cerrar antes de resolver no anuncia éxito ni cambia foco después. Errores JS vacíos.

HTTP no seguro real en Chromium: URL qa-copy.invalid con isSecureContext=false y navigator.clipboard ausente. La red se dirige exclusivamente al servidor/base descartable mediante rutas Playwright, manteniendo CSRF del servidor; sin settings de seguridad Django modificados ni flags que declaren el origen seguro. execCommand nativo confirma true dentro del callback de clic y se comprueba el texto completo leyendo independientemente el portapapeles desde localhost del mismo navegador. La lectura Windows normaliza CRLF a LF sólo en la comparación de QA; se conservan todos los caracteres/saltos/asteriscos. [Especificación W3C](https://www.w3.org/TR/clipboard-apis/) describe la normalización del sistema y las políticas de acceso.

Capturas whatsapp-copy-modern/http/manual-390 y modern-1280 inspeccionadas en tamaño de viewport: avisos operables dentro del modal, mensaje legible/desplazable, selección completa y botones sin recorte/overflow. El textarea conserva texto plano: negrita interpretada por WhatsApp al usar el mensaje. Las regresiones de axe, precios actuales, cantidades, salida en otra pestaña/fallback, cancelación y almacenamiento permanecen correctas. Todos los destinos wa.me se interceptaron; ningún envío ni cambio de datos comerciales. No se probó físicamente la Raspberry, Tailscale, Safari/Firefox ni un teléfono: la compatibilidad depende de la política del navegador y se conserva siempre la selección manual.

Actualización local en README: git pull --ff-only y docker compose up -d --build --no-deps web desde el proyecto existente; conservar configuración/identidad del stack y volúmenes PostgreSQL/media. Sin modelos/migraciones/dependencias ni cambios de infraestructura por estas dos mejoras.

## Catálogo compacto y presentaciones — 17/10/2026

Validación local final: **158 pruebas Django, 9 Node y 40 Chromium**, todas correctas y sin omisiones. Django completo en Docker/PostgreSQL con base de test; navegador completo con nueva base/media descartables de tests/browser_server.py, publicado sólo en localhost:8002 para evitar el puerto de ARCA DYS. check, Ruff, makemigrations --check --dry-run y git diff --check correctos. Sin dependencias/modelos de variantes nuevos y sin ejecutar migraciones/seed/import sobre la base comercial. No se ejecutó CI remoto ni se publicó esta iteración.

Comandos ejecutados: docker compose exec -T web python manage.py test --noinput; docker compose exec -T web ruff check .; docker compose exec -T web python manage.py check; docker compose exec -T web python manage.py makemigrations --check --dry-run; node --test tests/cart.test.cjs tests/hours.test.cjs; QA_BASE_URL=http://127.0.0.1:8002 con PLAYWRIGHT_BROWSERS_PATH=.qa/browsers y node --test tests/browser.spec.cjs. Contenedor QA separado con --no-deps y base/media temporales.

Migración histórica 0004→0005 comprobada con kg/0.10, unidad/2 y paquete/3: normaliza a 1 y compara exactamente todos los demás campos, incluyendo PK, timestamps, precios, imagen, texto y activo. Conserva edición de unidad anterior y rechaza altas nuevas con ella. Constraint DB impide incrementos 0.1/2; seis presentaciones aceptan 3 y bloquean 0.3. Fracciones v1 quedan intactas y bloquean recálculo/revisión/WhatsApp hasta corregir. No redondeo ni conversión de precios. CSV admite distintas unidades/descripciones, repite sin duplicar, rechaza pasos antiguos y conserva atomicidad/concurrencia/permisos/CSRF.

Browser comprueba + inicial, basura/1/+, −/2/+ y vuelta a vacío, foco tras borrar, nombre en aviso, botones 44×44, recarga y sincronización real catálogo/carrito/otra pestaña preservando mayorista manual. Fallo de setItem no cambia cantidad visible ni confirma agregado. Un resultado único mantiene máximo 300/340 px hasta 1920 px. Grilla: 320/360/390/430 una columna, 768 dos, 800/1000 tres, 1280 cuatro y 1440 cinco, sin scroll horizontal. Altas repetidas reales en Admin conservan campos y crean dos fichas independientes; tests Django incluyen imagen copiada, reemplazo sin borrar origen y token ajeno/modificado. Descripción distingue presentaciones en carrito y mensaje y exige nueva revisión al cambiar.

Se conservaron y ejecutaron regresiones completas de tarifas/precios vigentes, producto retirado/unidad cambiada, respuesta obsoleta, scroll/foco, revisión y cancelación, salida WhatsApp interceptada, fallback de copiado real HTTP, exportaciones CSV/PDF, importación, horarios, ubicación, imagen ampliada y 45 demos en base aislada. axe no detectó infracciones WCAG en las vistas/estados auditados. Capturas finales inspeccionadas: catalog-viewport-1440, presentation-single-desktop, presentation-variants-mobile y catalog-long-text-390. Miniaturas cuadradas recortan sólo vista previa; visor mantiene foto completa.

No se enviaron mensajes, no se accedió ni desplegó en Raspberry y no se modificaron datos/fotos comerciales. Teléfono/lector físicos, Safari/Firefox, zoom nativo e instalación Raspberry quedan como comprobaciones manuales; no se declaran ejecutadas. La guía CATALOGO_COMPACTO.md exige respaldo y ensayo en copia antes de migrar una instalación existente.

## Altura por fila, iconos exclusivos y seed local — ajuste posterior del 17/10/2026

39 pruebas Django de seed/vistas correctas, check/Ruff/makemigrations y diff correctos. Browser completo final: 40/40 correctas, sin omisiones. Ahora comprueba igualdad de altura y alineación inferior de controles para cada fila, en los nueve anchos existentes, además del ancho máximo. Comprueba ambas caras de cada estado: basura visible y − oculto con 1; − visible y SVG oculto con 2, incluida una cantidad fraccionaria v1 inválida. Header sólo número visible, manteniendo nombre accesible Carrito: 0 productos diferentes. Un bloque nuevo de comprobaciones se había insertado también en horarios por error; se retiró de ese escenario y se repitió la suite completa desde una DB nueva, con resultado correcto.

Operación real local autorizada: respaldo PostgreSQL custom e imágenes gzip, SHA-256, restauración del dump en dulce_salado_local_reset_check_20261017 y ensayo de 0005/reset/seed usando media temporal. Resultado 45 productos, 3 categorías y 45 imágenes; seis unidades, paso 1 y usuarios/configuración/horarios idénticos antes/después. Nueva copia inmediata previa al reset y aplicación en dulce_salado local, con el mismo resultado y repetición del seed sin cambios. IDs no reiniciados. Respaldos e informes privados en .qa/backups/20261017-reset-local/. No se modificó otro repositorio/base de negocio ni Raspberry.

Verificación adicional real en http://127.0.0.1:8000/ con contexto de navegador aislado: cinco columnas, fotos de los 12 productos visibles, todas las filas uniformes; 1→basura, 2→−, regreso a 1 y borrado sin ambos iconos. Sin overflow y axe sin infracciones en 320/390/430/768/1440. Capturas local-reset-1440, local-reset-trash y local-reset-minus inspeccionadas; archivo mobile/header también disponible. Contexto descartado sin cambiar el carrito del navegador del usuario. Servidor local normal conservado; QA/copia de ensayo se retiran al terminar. No envío de WhatsApp.

## Carrito compacto y precio público — ajuste final del 17/10/2026

Resultado final: 161 Django, 9 Node y 40 Chromium correctos; manage.py check, Ruff, makemigrations --check --dry-run y git diff --check correctos. La suite completa Chromium terminó con 40 pass/0 fail; el caso puntual de presentaciones también pasó por separado antes de la ejecución completa. Bases/media del runner aisladas, salidas WhatsApp interceptadas, sin mensajes enviados ni cambios en la instalación Raspberry.

Se verificó precio minorista único en catálogo/carrito/mensaje, ausencia de etiquetas/selectores/condiciones mayoristas, importes Decimal vigentes, conservación de datos mayoristas administrativos y conversión v1 con aviso y revisión aun con hash vigente. Controles derechos de 44 px; basura/− excluyentes con cambios desde botones o campo; edición de cantidades sin decimales visibles, eliminación con teclado o campo enfocado y sincronización entre pestañas.

Las pasadas anteriores detectaron expectativas de la ubicación vieja de la papelera y un caso real de cantidad anterior retenida al conservar foco en otra pestaña. Corregidos: borradores marcados sólo durante edición, limpieza al guardar y cantidades equivalentes comparadas numéricamente. Regresiones finales cubren edición seguida de −, eliminación con foco, respuesta atrasada, scroll, almacenamiento y navegación/copia/WhatsApp/Admin/CSV/PDF/horarios anteriores.

Verificación adicional sobre http://127.0.0.1:8000/ con contexto de navegador descartable: 45 demos conservados, precios iguales en catálogo/carrito, cantidades 1→2→1→eliminar, foco al quedar vacío, sin errores JS. Responsive/axe WCAG 2A/AA/2.1AA sin incidencias automáticas a 320/390/430/768/800/1440 px. Capturas privadas inspeccionadas: .qa/screenshots/retail-catalog-1440.png, retail-cart-390-trash.png, retail-cart-390-minus.png y retail-cart-1440-trash.png. La revisión automática no reemplaza una evaluación manual completa con tecnologías asistivas.

## Alineación y mensaje editable — 17/10/2026

Resultado final: 172 Django completos correctos, 6 de horarios repetidos después de añadir nombres accesibles al formset, 9 Node y 44 Chromium (44 pass/0 fail). manage.py check, Ruff, makemigrations --check --dry-run y git diff --check correctos. 0006 aplicada localmente tras respaldo de PostgreSQL. Tests de migración comparan productos, configuración previa, usuarios y horarios; restauran la última migración al terminar.

Nuevos casos: formatos personalizados/emojis, orden y campos requeridos, permisos, texto escapado, no interpretación de llaves de producto, omisión de líneas opcionales sin perder nombre/importes, formato externo inválido con fallback, configuración ausente sin escrituras, revisión faltante/cambiada antes de WhatsApp, mismo texto en preview/copia/URL. Edición real en Admin de QA, mensajes por defecto/custom, validación conservando valores previos y rechazo de cambio durante un diálogo abierto; navegación interceptada, sin envío.

Primera pasada detectó expectativas del botón Catálogo anterior y un fixture monetario sin refrescar; adaptados al nuevo comportamiento/datos de DB. Axe sobre el formulario comercial detectó campos sin nombre en los intervalos: add_fields añade etiquetas para día/apertura/cierre/DELETE, incluidas filas nuevas. La ejecución final completa verifica también esa pantalla sin incidencias automáticas. No se filtraron ni deshabilitaron reglas axe.

Verificación adicional sobre el sitio habitual 8000 con contexto descartable: 45 demos, alineación de títulos/descripciones/precios/controles por fila a 320/390/430/768/800/1280/1440 px, sin desbordes; header contextual, horarios conservados y aviso del carrito retirado. Axe WCAG 2A/AA/2.1AA sin incidencias automáticas en siete anchos. Capturas privadas inspeccionadas: aligned-catalog-1440.png, aligned-catalog-390.png, aligned-default-whatsapp-390.png, whatsapp-admin-editor-390.png y whatsapp-custom-review-390.png en .qa/screenshots/. Pruebas automatizadas en Chromium; no se afirma evaluación exhaustiva con lectores o teléfonos reales.

## Carga local con fotos y presentaciones sin prefijo — 17/10/2026

Completado por pedido expreso: 45 fichas sin [DEMO], 45 WebP independientes de las nueve fotos provistas, nombres repetidos por presentación y fotos correspondientes. Dietética 12/Cotillón 3/Repostería 30. Mismo título en 100 gr/kg/paquete y otras unidades admitidas, descripción/precio propio; marca identificable en foto y datos de simulación. Configuración, WhatsApp, usuarios y horarios conservados exactamente por huella; secuencias no reiniciadas. Respaldo DB/media, restauración y ensayo aislados, respaldo inmediato, aplicación local y repetición idempotente documentados en DATOS_PRUEBA_FOTOS.md.

Seeder con manifiesto v2 por categoría/título/unidad/descripción, sin usar título como identidad exclusiva. V1 se conserva y aborta hasta revisión; no apropiación automática de registros. --image-map opcional validado para fotos por título y varias vistas, manteniendo el reparto previo sin mapa y todas las guardas/rollback/archivos independientes. Sin cambios de modelos/migraciones/dependencias. Reset puntual sólo en .qa, no un comando general destructivo.

Verificación: 29 seed, 175 Django completos sin omisiones y 44 Chromium correctos; check/Ruff/migraciones/diff correctos. Prueba real local con fotos/variantes independientes y WhatsApp, cinco anchos/axe, capturas inspeccionadas y SHA-256 de originales intactos. La primera ejecución completa se interrumpió durante el mantenimiento; una auxiliar omitió Poppler, y la ejecución final completa sobre el contenedor habitual pasó las 175. Datos/backup/fotos privados ignorados por Git; copia de ensayo y QA retirados, sitio 8000 operativo. Sin mensajes enviados, publicación, acceso a Raspberry ni cambios en ARCA DYS.

## Encabezado, ubicación desplegable y sincronización — 17/10/2026

Verificación final: 177 pruebas Django completas sin omisiones, 9 Node y 46 Chromium correctas; check, Ruff, migraciones pendientes de modelo y diff sin incidencias. Comprobación adicional del sitio local con sus 45 productos/45 imágenes/3 categorías/configuración existente: nueve anchos (320/390/600/768/800/1049/1050/1280/1440), ambos paneles dentro del viewport, axe sin incidencias automáticas, búsqueda desde carrito, seis presentaciones por nombre, cantidades sincronizadas, redirecciones y cero peticiones externas/errores JS. Capturas privadas local-header-location-1440.png y local-header-hours-390.png inspeccionadas. Esto no sustituye una evaluación completa con lectores de pantalla o teléfonos reales.

Cobertura nueva: buscador/categorías globales con destinos GET desde carrito, conservación de filtros y fallback sin JS; retiro de subtítulo/página/iframe, dirección escapada, ausencia de dirección sin Maps falso, enlace exacto o búsqueda codificada con emoji/nombre accesible/otra pestaña segura; cierre con teclado/exterior/foco y redirecciones abiertas sin JS. Horarios publicados probados también a 320 px y en el límite 1050 px.

Una ejecución de 44 pasó; al agregar la navegación se detectó un fallo intermitente de cantidades entre pestañas. Reproducción controlada con una respuesta retenida y entrega tardía de storage: antes reaparecía un artículo eliminado (0→1); después de comparar el estado guardado contra submitted se conserva eliminado (0→0). Se incorporó esa regresión a la ejecución final de 46. Una comprobación privada inicialmente consultó innerText de un panel cerrado y se corrigió a textContent; el sitio no tenía una ausencia del emoji. QA temporal y sus datos se retiraron al terminar; la base local habitual no se reinicializó ni editó.

## Hover, espacio y pin del encabezado — 17/10/2026

Validación final del ajuste: 177 Django completos, 9 Node y 50 Chromium correctos, sin omisiones; check/Ruff/makemigrations --check/diff correctos. Las nuevas pruebas comprueban ancho máximo de búsqueda, acciones de 48 px/separación de 16 px, categorías sin íconos, pin SVG, flecha fija antes/después, apertura por hover sin mover foco, recorrido al panel, cierre al salir, cambio de panel/Escape, enlace enfocado persistente, teclado y pantalla táctil real emulada (tap abre/cierra/exterior). Fallback sin JS y filtros/carrito/WhatsApp siguen cubiertos en la suite completa.

Sitio local habitual: diez anchos (320/390/600/768/800/1049/1050/1280/1440/1920), ambos paneles dentro del viewport, sin desbordes ni incidencias automáticas axe WCAG 2A/AA/2.1AA, sin peticiones externas ni errores JS; 45 productos conservados. Capturas privadas header-hover-closed-1440.png, header-hover-location-panel-1440.png y header-hover-location-panel-390.png inspeccionadas. Se conserva foco visible por teclado. Esta revisión automática no afirma una auditoría completa de lectores o dispositivos reales.

Una primera prueba táctil intentaba tocar el contador de productos cubierto por el panel de horarios; se cambió el destino exterior al buscador visible por encima del panel. La ejecución final usa eventos reales de toque, no fuerza clics ni excluye reglas de accesibilidad. QA/base temporal retirados al terminar. Datos locales, imágenes, usuarios, horarios y configuración conservados.

## Carrito lateral en iframe y ajustes de foco — 17/10/2026

Verificación final: 180 Django completos, 9 Node y 59 Chromium correctos; 9 del grupo lateral repetidos tras añadir la eliminación del último artículo, también correctos. Ruff/check/makemigrations --check/diff correctos. Cobertura de SAMEORIGIN/frame mínimo/fallback, foco del buscador por mouse/Tab, centro limitado de Ubicación, geometría y scroll sin desplazar catálogo, pie fijo, lista larga, vacío/última eliminación, cantidades sincronizadas, toque/volver, Escape anidado, copiado real en iframe, revisión y cancelación de provisional WhatsApp, mensaje de origen/ventana incorrecta, fallo de carga y apertura desde aviso con retorno de foco.

Comprobación sobre el sitio local con seis presentaciones/fotos de Baño de repostería blanco: nueve anchos (320/390/430/600/768/800/1050/1280/1440), panel a la derecha o completo, total fijo al hacer scroll, sin desplazamiento inicial del catálogo, sin errores JS/peticiones externas/incidencias automáticas axe WCAG 2A/AA/2.1AA. Capturas privadas local-cart-drawer-1440.png, local-cart-drawer-390.png y local-location-centered-1440.png inspeccionadas. No se afirma evaluación exhaustiva con lectores o dispositivos físicos.

Se normalizaron CRLF nativos del portapapeles Windows al comparar mensajes, como en las pruebas existentes. El retorno desde Ver carrito detectó el disparador oculto al cerrar el aviso y el foco aún bloqueado por inert: se recupera el control visible después de cerrar dialog, sin desplazar scroll. Ambas situaciones tienen regresiones; no se forzaron clics ni filtraron reglas axe. Pruebas aisladas de WhatsApp interceptan navegación/provisional, sin enviar mensajes. Base/contenedor temporal de QA retirados al terminar; datos habituales conservados.

## Centrado responsive, avisos y footer — 17/10/2026

Verificación final: 181 Django completos, 9 Node y 63 Chromium correctos; check/Ruff/makemigrations --check/diff correctos. Grilla comprobada en doce anchos (320/390/520/600/700/740/768/800/1000/1050/1280/1440), igual altura por fila y centro con tolerancia inferior a 1 px. Avisos éxito/error centrados, acción inline en escritorio y textos largos sin desbordar en móvil. Carrito completo hasta 600 px y ancho esperado en ocho anchos hasta 1920. Footer: URL configurada/fallback, nueva pestaña segura, sin abrir el desplegable y disponibilidad cuando falta dirección.

Sitio local habitual: seis presentaciones con fotografías, doce anchos de grilla y cinco del carrito, sin errores JS ni incidencias automáticas axe WCAG 2A/AA/2.1AA. Capturas privadas local-centered-grid-740.png, local-centered-notice-1440.png y local-wide-cart-1440.png inspeccionadas. La prueba del enlace Maps intercepta la navegación por hostname/ruta para evitar cargar el servicio externo; no depende del contenido de Google. No se afirma evaluación exhaustiva con lectores o dispositivos físicos.

Se corrigió el localizador de la prueba del panel cerrado para leer su enlace aunque esté oculto. Las comprobaciones de URL/target/rel y clic del footer siguen activas. Base/contenedor temporal de QA retirados al terminar; 45 productos habituales conservados.

## Avisos arriba, recálculo estable y veinte por página — 17/10/2026

Verificación final: 182 Django completos, 9 Node y 66 Chromium correctos; grupo específico de centrado/carga (7) también correcto. check/Ruff/makemigrations --check/diff correctos. Pruebas de navegador verifican avisos al borde superior con texto centrado/acción inline y adaptación móvil, filas completas en las tres páginas de 45 fixtures a cinco columnas (1920/1440) y primeras páginas a cuatro columnas (1280), filtros/GET sin JS/rangos/IDs sin repetir.

Nueva regresión detiene respuestas reales de recálculo y compara geometría antes/durante/después al sumar/restar en /carrito/ y en iframe: lista, primera ficha y resumen idénticos. role=status permanece accesible y recortado a 1 px, aria-busy/revisión bloqueada durante consulta y habilitada después. No se desactiva la verificación del servidor para ocultar el salto.

Sitio habitual con fotografías: 45 IDs distintos en páginas 20/20/5, filas de cinco completas a 1920x1080 y ocho anchos (320/390/520/740/1000/1280/1440/1920) sin desbordes, errores JS ni incidencias automáticas axe WCAG 2A/AA/2.1AA. Capturas privadas local-complete-rows-3-1920.png, local-top-notice-1920.png y local-cart-no-loading-space-1920.png inspeccionadas. No se afirma auditoría exhaustiva de dispositivos físicos/lectores. QA temporal retirado; datos locales conservados.

## Carrito silencioso, actualizaciones parciales y listas largas — 17/10/2026

Verificación final: 184 Django completos, 9 Node y 72 Chromium correctos; seis del grupo silencioso repetidos durante el ajuste y también correctos. check/Ruff/makemigrations --check/diff y sintaxis JS correctos. Nuevo mensaje por producto/acción, cruz SVG de color heredado para cuatro estados, carga sin aviso, cantidades/eliminación silenciosas, identidad de fotos/títulos/otras fichas, observador sin mutaciones en fila intacta y cero navegaciones del iframe al editar. Revisión con icono accesible a la derecha, sin párrafos retirados y total dentro del mensaje; copiado real/API/fallback conservados.

Lista larga probada en seis anchos automatizados y con las 45 fichas/fotos locales en ocho (320/390/600/768/1050/1280/1440/1920): controles y miniaturas dentro de cada borde, filas separadas, scroll propio/pie fijo y eliminación correcta. Sin errores JS ni incidencias automáticas axe WCAG 2A/AA/2.1AA. Capturas privadas local-long-cart-top-1920.png, local-long-cart-bottom-390.png, local-review-copy-icon-390.png y local-green-notice-1920.png inspeccionadas. Sin auditoría exhaustiva de teléfonos físicos/lectores de pantalla. Pruebas de WhatsApp interceptadas, sin envíos.

Se actualizó la antigua expectativa de éxito tras eliminar en /carrito/ para exigir ausencia del aviso. El fixture de identidad selecciona IDs distintos aunque queden menos fotos después de otras pruebas; conserva comprobación de foto real y resto de nodos sin mutaciones. La prueba de total redundante se limita a párrafos de revisión para no confundir Subtotal estimado dentro del texto del pedido. QA/base temporal retirados; 45 productos habituales conservados.

## Zoom limpio, revisión y cantidades — 17/10/2026

Verificación final: 188 Django completos, 9 Node y 77 Chromium correctos; ocho de visor/cantidad/botón repetidos tras retirar aviso corregido, también correctos. check/Ruff/makemigrations --check/diff y sintaxis JS correctos. Migración 0007 probada con default anterior, formato personalizado con frase y formato sin frase: sólo cambia la etiqueta solicitada y conserva otros campos/productos. Estado de migraciones local al día.

Navegador comprueba cruz blanca sin borde/fondo fuera de foto, fondo 85%, sin marco blanco, proporción/naturalidad/límites en catálogo y carrito, foco/teclado/Escape/clic fuera. Cantidades negativas/cero/decimales sólo anuncian arriba, sin bloque visible, con aria-invalid/descripción accesible, revisión bloqueada y mínimo 1 válido. Aviso anterior se retira al corregir. Botón conserva opacidad 1 y nodo durante recálculo mientras mantiene bloqueo seguro. Vista previa sin región retirada ni referencia ARIA huérfana, diez líneas, copiar junto al label y Volver/Enviar a WhatsApp; total en mensaje y Subtotal actualizados. Copiado real y revalidación/serial/storage/errores/WhatsApp interceptado siguen cubiertos sin enviar mensajes.

Sitio habitual con fotos locales: zoom en ocho anchos (320/390/600/768/1050/1280/1440/1920), visor del carrito/revisión en escritorio y móvil, negativo sólo arriba y corrección a 1; sin errores JS ni incidencias automáticas axe WCAG 2A/AA/2.1AA. Capturas privadas local-zoom-borderless-1920.png, local-cart-zoom-borderless-390.png, local-review-clean-390.png y local-quantity-negative-toast-390.png inspeccionadas. No sustituye auditoría exhaustiva de dispositivos físicos/lectores.

QA/base temporal retirados al terminar. La captura final se regeneró después de corregir la permanencia del aviso de cantidad inválida tras restaurar 1. Los 45 productos, usuarios y horarios habituales se conservan; respaldo antes/después de configuración en .qa privado.

La prueba rápida entre cerrar visor y usar otro control detectó una restauración tardía de foco que podía reabrir la imagen. Corregida en catalog.js y cinco del grupo de zoom repetidos correctamente antes de la suite final completa.


## Pesos enteros, cajas y avisos — 18/10/2026

194 tests Django completos sin omisiones, 9 Node y 81 Chromium correctos. Check, Ruff, makemigrations --check --dry-run y diff --check correctos. La primera suite de navegador detectó expectativas anteriores (sin input, avisos inline y centavos); se actualizaron esas expectativas y el juego CSV. La ejecución final completa con fixtures limpias pasó todos los escenarios, incluido copiado real, revalidación, sincronización, errores de conexión/storage, fotos y flujo WhatsApp interceptado sin enviar mensajes.

Cobertura nueva: ambos precios en Admin/CSV rechazan fracciones, .00/coma, signos y exponentes; save rechaza centavos antes de que numeric redondee; migración conserva nulos/fotos/fechas/configuración e identidades y trunca 100.99→100, 0.99→0 y límites anteriores. Formato y cálculo exactos en catálogo/carrito/WhatsApp/exportaciones. Cantidad boxed en catálogo y carrito; bloqueo de teclado/paste/IME antes de mutar, rechazo completo de 9,1 sin convertir a 91, cero/negativos/fracciones de API/storage bloquean revisión y sólo muestran diagnóstico arriba. Mantener mínimo 1, navegación/caret, borradores y sincronización.

Aplicación local: dump PostgreSQL privado en .qa/backups/20261018-integer-prices/database.dump (45.292 bytes, SHA-256 88155a867f43631404270c98d6ce77c0f3b64a8834263d259ae0f40b0849c3ba). Se restauró y migró una copia aparte; comparación exacta antes/después y ensayo idénticos: 45 productos conservados, 6 con fracciones descartadas, sólo retail/wholesale cambiados; fotos/manifiesto/categorías/usuarios/configuración/horarios intactos. Reportes before/after/verification privados con datos sensibles, ignorados por Git. Reversa de esquema no recupera centavos: usar el respaldo si se requiere restaurar esos importes.

Sitio local comprobado con las fotos del dueño en 320/390/600/768/1050/1280/1440/1920 px y panel en 320/390/768/1920; cero infracciones axe A/AA/2.1 y errores JS, sin desbordes, precios enteros y cajas alineadas. Capturas locales .qa/screenshots/local-whole-* inspeccionadas. Sin limpieza/seed, cambios en fuentes originales, commit/push, mensajes enviados ni acceso/despliegue Raspberry. QA temporal y base de ensayo retirados; sitio habitual en 8000.


## WhatsApp: integridad Unicode y pedido legible — 18/10/2026

Causa reproducida con número ficticio/mensaje sintético: wa.me alteró 🛍️/💰/📌 a U+FFFD al redirigir con ambos codificadores de espacios. api.whatsapp.com/send mantuvo el texto exacto en su enlace a Web. Cambio de endpoint y codificación única quote UTF-8 estricta, sin tocar la lógica de revalidación/cancelación/popup/stock/precios. No se enviaron mensajes reales.

Usuario confirmó incluir el formato adjunto. Seis unidades, singular/plural, contenido individual sin multiplicación, marca opcional, negrita WhatsApp para nombre/subtotal/total, precio por unidad sin tarifa, un separador y cierre 📌. Sólo descripción libre disponible; reconocer formas completas de peso/composición y preservar otras redacciones en línea adicional, sin inventar contenido. Aliases nuevos compatibles con formatos anteriores.

203 Django completos sin omisiones y 84 Chromium correctos; pruebas de seis casos del adjunto (total $247.400), variantes mismo título, marcas/ausencias/contenido/plurales/ambigüedad, validación y conservación de formatos propios/migraciones, Unicode/ZWJ/acentos/reservados y HTML del enlace. Navegador valida botón y respaldo desktop/móvil, texto/copia/link iguales, límites/revalidación/cancelación y lo demás existente. Primeras ejecuciones detectaron expectativas del formato anterior; ajustadas sin cambiar los cálculos. Ruff/check/makemigrations/diff correctos.

0009 aplicada sólo local: respaldo de BusinessSettings en .qa/backups/20261018-whatsapp-format (1.231 bytes, SHA-256 6aa530c1f8c0a5afd2338179ddcf886f1e000c342cbd984ef41eb0286d8bb65e), comparación sólo dos defaults y hashes íntegros de 45 productos, categorías, usuarios, horarios y media/manifiesto. Sin reset/reseed. Formatos propios no se sobrescriben.

Pedido local de dos presentaciones de Baño de repostería blanco: 4 cajas de 5 kg + 2 packs de 3 paquetes de 500 g, total $239.200; textarea, copiado real (normalizando CRLF de Windows) y destino interceptado idénticos. Capturas local-whatsapp-readable-1920/390 inspeccionadas, cero axe A/AA/2.1 y errores JS. QA/base temporal retirados; normal 8000 operativo. Sin cambios de infraestructura, despliegue Raspberry, commit/push ni envío real. La recepción/renderizado final en la app de WhatsApp la comprueba el usuario al enviar.
