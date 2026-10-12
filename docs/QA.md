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
