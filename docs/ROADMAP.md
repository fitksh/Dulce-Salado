# Roadmap

Trabajar secuencialmente y actualizar el estado sólo al terminar y verificar cada etapa. No implementar etapas futuras por anticipado. En esta etapa se trabaja sólo en `main`.

- [x] Fase 0 — Definir alcance, decisiones técnicas y límites del MVP.
- [x] Fase 1 — Esqueleto y auditoría verificados en Docker Python 3.12/PostgreSQL: 7 tests, checks y Ruff OK; migraciones base aplicadas. CI se comprueba después de publicar.
- [x] Fase 2 — Category/Product, migraciones, Admin con permisos e imagen única validada/optimizada. Verificado en Docker: 20 tests, checks y Ruff OK. Unidades e incrementos autorizados documentados.
- [x] Fase 3 — Catálogo público mobile-first, búsqueda, categorías y estados vacíos; 27 tests/check/Ruff OK. QA visual final en fase 6.
- [x] Fase 4 — Carrito local, cantidades/tarifa, refresco de datos y cálculos Decimal; 34 tests Django y 4 Node/check/Ruff OK.
- [x] Fase 5 — Revisión y aviso obligatorio, mensaje completo wa.me, validación final y bloqueo sin teléfono; 39 tests Django y 4 Node/check/Ruff OK, sin envío real.
- [x] Fase 6 — QA verificado localmente y en CI: 42 tests Django, 4 Node y 11 comprobaciones Chromium; axe sin infracciones en vistas verificadas. Publicado en main; CI success run 38086302160. Pruebas comerciales de teléfono/lector real detalladas en QA.md.
- [ ] Fase futura — VPS, dominio, HTTPS, proxy estáticos/media, backups y despliegue; fuera del alcance actual.

## Criterios de avance
Completar una fase significa código integrado en `main`, comprobaciones ejecutadas y registradas, criterios funcionales verificados y documentación actualizada. Si CI o tests no pudieron ejecutarse, el estado es pendiente de verificación.

## Continuación autorizada
Completar secuencialmente el MVP según la solicitud de desarrollo autónomo del 2026-10-10. Las decisiones de unidades, incrementos, mayorista opcional y centavos están autorizadas y registradas en `EXECUTION_STATUS.md`.

MVP completado el 2026-10-10. Próximo paso: pruebas locales del dueño siguiendo README y QA.md, con productos/precios y WhatsApp reales. Infraestructura de producción permanece fuera de alcance.

## Etapa complementaria UX/UI autorizada el 2026-10-10

Conservar diseño y MVP. Ejecutar secuencialmente, sin ampliar precios, carrito, WhatsApp o infraestructura fuera de lo solicitado.

- [x] Tarea 1 — Logo provisto, header compacto, iconos de carrito/Instagram y eliminación de dos textos; 15 tests afectados y 11 comprobaciones Chromium OK.
- [x] Tarea 2 — Búsqueda por descripción con prioridad, categorías móviles, controles táctiles, condiciones discretas y placeholder; 17 tests afectados, 5 Node y 12 comprobaciones Chromium OK.
- [x] Tarea 3 — Scroll estable del carrito, mensajes consistentes y confirmaciones nativas Admin; 22 tests afectados, 5 Node y 13 comprobaciones Chromium OK.
- [x] Tarea 4 — Exportar CSV completo/filtrado desde Admin con permisos y protección de fórmulas; 13 tests afectados y 14 comprobaciones Chromium OK.
- [x] Tarea 5 — Configuración comercial única, dirección y Cómo llegar; migración 0003 aplicada, 23 tests afectados y 15 comprobaciones Chromium OK.
- [x] Tarea 6 — Intervalos semanales, validaciones y estado abierto/cerrado actualizado localmente; migración 0004 aplicada, 33 tests afectados, 7 Node y 16 comprobaciones Chromium OK.
- [x] Tarea 7 — QA completo: 60 Django, 7 Node y 16 Chromium OK, responsive/axe/regresiones; publicado en main, CI success run 38095823292 (incluye corrección de foco tras Escape).

Etapa complementaria completada y publicada. Historial MVP conservado. Siguiente paso: revisar datos comerciales y pruebas manuales reales de teléfono/lector/Maps/Excel según QA.md. Despliegue de producción permanece fuera de alcance.

## Segunda iteración UX/UI autorizada

- [x] Tarea 1 — Limpieza, header/horarios flotantes, categorías automáticas, footer y toolbar móvil; 28 Django, 7 Node y 16 Chromium OK.
- [x] Tarea 2 — Mapa embebido responsive y navegación externa; 15 Django y 16 Chromium OK, recurso externo interceptado.
- [x] Tarea 3 — Ampliación de imagen con dialog reutilizable; 10 Django y 17 Chromium OK, teclado/foco/axe.
- [x] Tarea 4 — Condiciones mayoristas con destacado suave; 24 Django y 17 Chromium OK, contraste axe.
- [x] Tarea 5 — Notificaciones flotantes y errores persistentes; 24 Django, 7 Node y 18 Chromium OK, scroll/foco/timers/axe.
- [x] Tarea 6 — WhatsApp en nueva pestaña con fallback seguro; 14 Django, 7 Node y 20 Chromium OK, cancelación/errores/precios vigentes.
- [x] Tarea 7 — QA, documentación y publicación final; 63 Django, 7 Node y 22 Chromium OK, cinco anchuras/axe y CI success run 38101095717.

Segunda iteración completada y publicada en main. Sin nuevas dependencias/modelos/migraciones ni cambios de reglas comerciales. Entorno local actualizado y datos conservados. Siguiente paso: prueba real en teléfono/lector, carga externa Maps y configuración comercial según QA.md.

## Correcciones visuales puntuales

- [x] Tarea 1 — Miniaturas completas y modal sólo foto/cierre; 10 Django, 22 Chromium y Ruff OK; cinco anchuras/axe y capturas inspeccionadas.
- [x] Tarea 2 — Header en fila de tres regiones en escritorio y columna en móvil; 16 Django, 7 Node y 22 Chromium OK.
- [x] Tarea 3 — Dirección, botón y mapa en una región responsive; 16 Django, 22 Chromium y Ruff OK.
- [x] Tarea 4 — Footer centrado en todas las pantallas; 10 Django y 22 Chromium OK, cinco capturas inspeccionadas.
- [x] Tarea 5 — QA completa, capturas, documentación y publicación final; 63 Django, 7 Node y 22 Chromium OK, CI success run 38105183767.

Correcciones visuales completadas y publicadas; capturas reales inspeccionadas, main sincronizada, entorno local actualizado y datos conservados. Próximo paso: pruebas locales en teléfono real según README/QA. Historial anterior intacto; infraestructura futura fuera de alcance.

## Nueva iteración UX/UI y datos de prueba

- [x] Tarea 1 — Logo de 64 px, navegación agrupada y separadores semanales; Django y Chromium correctos.
- [x] Tarea 2 — Ubicación, redirección permanente e información centrada.
- [x] Tarea 3 — Carrito compacto, miniaturas y recuperación contextual.
- [x] Tarea 4 — Catálogo compacto y paginación de 12 productos.
- [x] Tarea 5 — Limpieza visual de revisión WhatsApp.
- [x] Tarea 6 — Seed manual de 45 productos ficticios, simulación y limpieza seguras.
- [x] Tarea 7 — QA completa, documentación, publicación y CI; 78 Django, 7 Node y 24 Chromium OK, CI success 38115967060.

Nueva iteración completada y publicada en main. Datos comerciales conservados, sin nuevos modelos/migraciones/dependencias; entorno local actualizado. Próximo paso: recarga Ctrl+F5, pruebas reales en teléfono/lector y dirección completa desde Admin. Seed opcional manual en DEBUG según README; no aplicado automáticamente. Infraestructura futura permanece fuera de alcance.

## Exportación PDF y ajustes puntuales

- [x] Tarea 1 — Ubicación en header y responsive desde 320 px.
- [x] Tarea 2 — PDF Admin con/sin fotos, filtros/permisos y revisión visual.
- [x] Tarea 3 — Papelera accesible, comportamiento existente.
- [x] Tarea 4 — Foto/columna desktop, móvil y recálculos conservados.
- [x] Tarea 5 — QA completa, PDFs de ejemplo, documentación y CI.

Exportación PDF y ajustes completados/publicados en main, cinco tareas con CI success. 88 Django, 7 Node, 25 Chromium, check/Ruff y migraciones correctos; dos PDFs ficticios A4 inspeccionados en todas sus páginas. Entorno local actualizado y registros/fotos conservados. Próximo paso: Admin/filtros/ambas descargas y pruebas locales de carrito responsive, visor/impresora, zoom y teléfono/lector según README/QA. Sin modelos/migraciones ni trabajo de fases futuras.

## Nuevas exportaciones PDF, imágenes e importación CSV

- [x] Tarea 1 — PDF tabla compacta; 17 PDF/CSV, 25 Chromium y revisión de seis páginas correctos.
- [x] Tarea 2 — PDF tabla con imágenes; 19 PDF/CSV, 25 Chromium y siete páginas inspeccionadas.
- [x] Tarea 3 — Marcos cuadrados; 24 Django, 25 Chromium y cinco anchuras/fotos reales inspeccionadas.
- [x] Tarea 4 — Motor CSV de altas y validaciones; 19 tests CSV correctos. Interfaz/confirmación en tarea 5.
- [x] Tarea 5 — Admin, preview/confirmación firmada y plantilla/documentación; 49 CSV/PDF y 26 Chromium correctos.
- [x] Tarea 6 — QA completa y publicación final; 126 Django, 7 Node, 26 Chromium, 19 páginas PDF y cinco anchuras inspeccionadas, CI success.

Las seis tareas están completas y publicadas en origin/main, todas con CI success (detalle en EXECUTION_STATUS). Sin modelos/migraciones/dependencias nuevos ni cambios comerciales/fotográficos. Los cambios locales anteriores del propietario se conservan fuera de commits. Próximo paso: Ctrl+F5, Admin → Productos → ambas tablas PDF; descargar/preparar plantilla CSV, analizar/revisar y confirmar las altas deseadas según README. Impresora, Excel/Sheets y teléfono/lector propios quedan como pruebas manuales; no se anticipó ninguna fase futura.

## Ajustes puntuales de imágenes, catálogo, carrito y PDF

- [x] Tarea 1 — Visor ajustado a proporción intrínseca; 33 Django, 26 Chromium y 18 capturas de seis viewports correctos.
- [x] Tarea 2 — Cuatro columnas a 1280/1440 px, 1/2/3 intermedias; 13 Django y 26 Chromium correctos, controles/textos inspeccionados.
- [x] Tarea 3 — Foto de carrito centrada en escritorio; 11 Django, 5 Node y 26 Chromium correctos, móvil intacto.
- [x] Tarea 4 — Logo de 16 mm en los cuatro PDF, foto centrada/etiquetas escapadas en negrita en listas; 23 PDF/CSV, 26 Chromium y 19 páginas inspeccionadas.
- [x] Tarea 5 — QA completa: 130 Django, 7 Node, 26 Chromium, 19 páginas PDF y capturas web correctos; publicación con CI success.

Iteración completa y publicada en origin/main, cinco tareas con CI success (detalle en EXECUTION_STATUS). Conserva arquitectura, datos/reglas comerciales, CSV y archivos de fotos. Cambios locales previos del propietario excluidos de commits. Próximo paso: Ctrl+F5, catálogo/visor/carrito y cuatro PDF filtrados desde Admin según README; impresión física, teléfono/lector y zoom nativo quedan para el entorno del usuario.

## Seed manual con fotografías locales

- [x] Ampliar seed_demo_catalog con --images-dir opcional, lectura inmediata validada y reparto reproducible/equilibrado; copias WebP independientes mediante el procesamiento existente, originales intactos.
- [x] Conservar DEBUG/simulación/--apply, 45 especificaciones, categorías y datos existentes; manifiesto compatible, idempotencia y limpieza conservadora de copias propias tras commit. Rollback de altas/archivos y restauración del manifiesto ante errores comprobados.
- [x] Validación en Docker local: 146 Django completos (26 seed y 7 imágenes), check/Ruff correctos y sin migraciones. Fixtures temporales prueban nueve fotos cinco veces cada una, conversión/EXIF/transparencia, validación, permisos/enlaces, simulación, repetición, fallos de base/storage/conversión/manifiesto y limpieza de compartidas/ediciones/ajenos.

Sólo comando, tests, README y este seguimiento; sin fotos añadidas a Git, dependencias/modelos/migraciones ni cambios de Docker/interfaz. No se aplicó el seed al catálogo comercial. Próximo paso: disponer del código actualizado en el contenedor Raspberry Pi/Portainer y seguir README: simular la limpieza si ya hay demos, confirmar los borrados deseados y luego simular/aplicar --images-dir /app/demo-images con DJANGO_DEBUG=1. Montaje de origen sólo lectura y media persistente existentes.

## Copiado y formato del mensaje WhatsApp

- [x] Clipboard API principal y fallback copy síncrono sobre el textarea existente cuando falta la API; rechazo moderno también intenta fallback. Éxito sólo confirmado, selección manual si falla, foco/scroll conservados y avisos duplicados/tardíos descartados.
- [x] Formato del servidor con títulos numerados/negrita, marca opcional, tarifa/precio/cantidad/subtotal en líneas separadas, divisor Unicode y total destacado; aviso/cierre exactos y mismo texto íntegro en vista previa, copia y wa.me. Marcadores de nombres/marcas neutralizados sólo al presentar.
- [x] 19 Django afectados y 149 completos, 7 Node y 35 Chromium correctos; check/Ruff y migraciones OK. Copiado real moderno y HTTP no seguro sin Clipboard API, errores/fallback/manual, contenido largo, foco/modal y regresiones de navegación/comercio verificados. Capturas 390/1280 inspeccionadas; detalle en QA.

Cambios limitados a cart.js/whatsapp.py, sus pruebas y documentación; sin modelos/dependencias/configuración de seguridad ni Docker, cálculos o localStorage nuevos. Pruebas sólo sobre datos aislados, sin enviar WhatsApp. Próximo paso: actualizar el mismo proyecto/stack Raspberry Pi conservando PostgreSQL/media según README, Ctrl+F5 y copiar/pegar desde la IP local o Tailscale; la política del navegador puede exigir selección manual.

## Catálogo compacto y presentaciones — 2026-10-17

- [x] Cards compactas, estados +/basura/− y sincronización sin perder tarifa manual.
- [x] Seis unidades de alta, incremento 1 en modelos/DB/CSV/carrito, compatibilidad sin convertir unidades/precios y migración probada.
- [x] Alta repetida precargada con imagen independiente y retiro de continuar editando.
- [x] Hasta cinco columnas y máximo de ancho para resultado único; teclado, responsive y errores de almacenamiento.
- [x] QA local completa: 158 Django, 9 Node y 40 Chromium; check/Ruff/migraciones/diff correctos, capturas inspeccionadas y documentación de actualización. Evidencia en EXECUTION_STATUS.

Despliegue en Raspberry excluido; pasos manuales y respaldo/ensayo en CATALOGO_COMPACTO.md. Cambios locales en main; no se declara publicación ni CI de esta iteración.

## Ajuste posterior: filas, iconos, header y carga local — 17/10/2026

- [x] Alturas iguales por fila según la card más alta y controles al pie.
- [x] SVG basura y − nunca visibles juntos; header sólo icono/contador con nombre accesible.
- [x] Seed de 45 productos con seis unidades/paso 1; respaldo completo, ensayo restaurado y reinicialización local expresamente solicitada, conservando acceso/configuración/horarios y sin reiniciar IDs.
- [x] 39 Django y 40 Chromium correctos; verificación local con axe en cinco anchos, capturas inspeccionadas y documentación. Demos e imágenes fuera de Git; sin Raspberry, publicación ni CI remoto.

## Carrito compacto y precio único — ajuste final del 17/10/2026

- [x] Controles a la derecha en catálogo/carrito, basura con 1 y − con más de 1, + disponible y espacios reducidos.
- [x] Sólo precio minorista público, sin etiqueta ni selector; mismo importe en cálculo y WhatsApp. Mayorista administrativo preservado.
- [x] Compatibilidad de carritos anteriores con aviso/revisión, cantidades enteras/correcciones, sincronización y foco.
- [x] 161 Django, 9 Node y 40 Chromium correctos; check/Ruff/migraciones/diff correctos. Sitio local comprobado con axe en seis anchos y capturas inspeccionadas. Sin cambios de base ni despliegue Raspberry.

## Alineación y mensaje editable — 17/10/2026

- [x] Bloques de título, descripción y precio alineados por fila, sin recortes y con controles a la derecha.
- [x] Header contextual, horarios sin texto Ver horarios y retiro del aviso de persistencia del carrito.
- [x] Dos formatos editables en Admin, emojis/viñetas/total iniciales, validación de campos, vista previa y revisión de cambios antes de WhatsApp.
- [x] Migración aditiva 0006 aplicada localmente con respaldo; conservación de datos probada.
- [x] 172 Django completos, 6 de horarios posteriores, 9 Node y 44 Chromium correctos; check/Ruff/migraciones/diff correctos, siete anchos con axe y capturas inspeccionadas. Entorno QA retirado, datos locales conservados, sin despliegue Raspberry.

## Nueva carga local con fotografías — 17/10/2026

- [x] 45 fichas sin prefijo, títulos compartidos y unidades/presentaciones independientes con fotos correspondientes de las nueve fuentes.
- [x] Seeder idempotente con manifiesto por presentación, guardas y mapa de fotos; 29 regresiones correctas.
- [x] Respaldo completo y restauración/ensayo, aplicación local conservando usuarios/configuración/horarios e IDs no reutilizados.
- [x] 175 Django y 44 Chromium correctos, comprobaciones de proyecto y verificación real de variantes/fotos/carrito/WhatsApp/axe en cinco anchos; documentación y capturas inspeccionadas. Sin Raspberry ni publicación.

## Encabezado y ubicación desplegable — 17/10/2026

- [x] Marca sin subtítulo, buscador integrado, categorías debajo, Ubicación/Horarios/carrito y retorno contextual al catálogo.
- [x] Dirección y enlace emoji Maps en desplegable accesible; página/iframe retirados y URLs antiguas con 301 al panel abierto, también sin JS.
- [x] Horarios/configuración y 45 fichas locales conservados; protección contra respuesta vieja que restaura eliminaciones entre pestañas, con regresión reproducible.
- [x] 177 Django, 9 Node y 46 Chromium correctos; comprobaciones de proyecto y nueve anchos locales con axe, capturas inspeccionadas. QA temporal retirado; sin migraciones nuevas ni despliegue Raspberry.

## Encabezado: espacio y hover — 17/10/2026

- [x] Buscador hasta 600 px, controles de escritorio mayores/separados y categorías sólo texto.
- [x] Chevrons fijos hacia abajo y pin SVG en Ubicación/Maps, sin emoji rosado.
- [x] Apertura por mouse con recorrido seguro/cierre al salir, foco protegido/Escape; teclado/toque/fallback sin JS conservados.
- [x] 177 Django, 9 Node y 50 Chromium correctos; comprobaciones de proyecto y diez anchos locales con axe/capturas inspeccionadas. QA temporal retirado, sin cambios de datos/migraciones ni despliegue Raspberry.

## Carrito lateral en iframe — 17/10/2026

- [x] Buscador sin contorno al clicar con foco de teclado conservado; ubicación centrada y limitada al viewport.
- [x] Panel derecho sin desplazar catálogo, fondo difuminado, lista desplazable y total/WhatsApp fijos; pantalla completa móvil con volver/cruz/exterior/Escape.
- [x] Vacío con total cero y Agregar productos; sincronización/copiado/revisión y cancelación de provisional al cerrar, con fallback directo y SAMEORIGIN.
- [x] 180 Django, 9 Node y 59 Chromium correctos, más 9 del panel tras la última ampliación; comprobaciones de proyecto y nueve anchos locales con axe/capturas inspeccionadas. QA retirado, sin migración ni cambio de datos/despliegue Raspberry.

## Centrado responsive y lectura — 17/10/2026

- [x] Una/dos/tres columnas centradas, conservando ancho máximo y altura por fila.
- [x] Carrito al 46% en escritorio, mínimo 520 px y completo hasta 600 px.
- [x] Avisos centrados en ambos ejes, acción inline cuando cabe y adaptación sin desbordes.
- [x] Footer Ubicación abre Maps directamente; configuración faltante sin enlace ficticio.
- [x] 181 Django, 9 Node y 63 Chromium correctos; comprobaciones del proyecto, doce anchos locales y axe/capturas inspeccionadas. QA temporal retirado, datos locales conservados; sin migración ni despliegue Raspberry.

## Aclaración de avisos y filas completas — 17/10/2026

- [x] Avisos arriba; sólo su contenido centrado, acción en la misma fila cuando cabe. Reemplaza el centrado vertical de la iteración anterior.
- [x] Consulta de catálogo sólo accesible, sin espacio visual variable ni saltos al sumar/restar.
- [x] Paginación de 20 para completar filas de cuatro/cinco; 45 resultados en 20/20/5, filtros/orden/GET conservados.
- [x] 182 Django, 9 Node y 66 Chromium correctos, más 7 específicos; comprobaciones de proyecto y ocho anchos locales con axe/capturas inspeccionadas. QA temporal retirado; datos conservados, sin nuevas migraciones/despliegue Raspberry.

## Carrito silencioso y actualización parcial — 17/10/2026

- [x] Retirar éxitos de cantidad/eliminación dentro del carrito y aviso de carga al abrir.
- [x] Mensaje de catálogo solicitado, cruces SVG del tono semántico para todos los avisos.
- [x] Conservar fotos/títulos/otras fichas y scroll al recalcular; actualizar datos necesarios con validación vigente.
- [x] Lista extensa sin compresión ni controles superpuestos, total fijo fuera del scroll.
- [x] Copiar como icono a la derecha; quitar total/párrafo redundantes de revisión.
- [x] 184 Django, 9 Node y 72 Chromium correctos; seis específicos repetidos, comprobaciones de proyecto y 45 fichas locales en ocho anchos con axe/capturas inspeccionadas. QA retirado, datos conservados; sin nuevas migraciones ni despliegue Raspberry.

## Zoom limpio y revisión — 17/10/2026

- [x] Imagen sin marco, fondo oscuro y cruz blanca sutil fuera de la foto en catálogo/carrito, con foco/cierre accesibles.
- [x] Botón de revisión con aspecto estable durante recálculo; Total como título.
- [x] Retirar región estática de advertencia, Volver/Enviar a WhatsApp, diez líneas y copiar junto al label.
- [x] Subtotal en formatos iniciales/guardados mediante 0007 conservadora, aplicada local con respaldo/comparación.
- [x] Mínimo 1 confirmado: enteros positivos, negativo exacto y errores sólo arriba; retiro del aviso al corregir, sin redondeo.
- [x] 188 Django, 9 Node y 77 Chromium correctos, ocho específicos repetidos y comprobaciones de proyecto; ocho anchos locales con axe/capturas inspeccionadas. QA retirado; datos conservados, sin despliegue Raspberry.


## Pesos enteros y sólo dígitos — 18/10/2026

- [x] Formato/cálculos/schema/precios Admin/CSV/PDF/WhatsApp/seed sin centavos.
- [x] Migración que descarta centavos antes de alterar precisión; validación de fracciones futuras.
- [x] Cajas de cantidad en catálogo/carrito, filtro de símbolos por teclado/pegado/móvil, mínimo 1.
- [x] Diagnósticos del pedido exclusivamente arriba, con validación/foco/revisión preservados.
- [x] 194 Django, 9 Node y 81 Chromium correctos; check/Ruff/migraciones/diff correctos. Base local respaldada/restauración ensayada, 45 fichas conservadas y 6 con centavos descartados. Ocho anchos locales y cuatro del panel, axe/JS sin errores y capturas inspeccionadas. QA retirado; sin Raspberry.


## WhatsApp: emojis y formato del pedido — 18/10/2026

- [x] Causa de emojis reproducida en redirección externa con texto ficticio; enlace directo UTF-8 y pruebas de ida completa.
- [x] Formato adjunto: seis unidades, singular/plural, marca opcional, contenido sin multiplicar, pesos enteros/negritas y un separador/cierre nuevo.
- [x] Gramática completa conservadora y fallback sin perder texto; aliases compatibles y validación del formato editable.
- [x] 0009 aplicada local con respaldo/comparación: sólo defaults, 45 fichas/fotos/precios y demás configuración conservados.
- [x] 203 Django y 84 Chromium correctos; pedido local del ejemplo, copiado real y destino interceptado coincidentes, axe/JS sin errores en desktop/móvil. QA retirado, sin envío real ni Raspberry.


## Corrección CI y publicación de la versión local — 18/10/2026

- [x] Checkout local identificado en Documents/GitHub/Dulce-Salado, main limpio y sin divergencia con origin/main (8e2f151); ningún cambio local descartado.
- [x] Fallo de Actions 39143824791 diagnosticado: las métricas de la fuente Linux desbordan los controles del header a 320 px y provocan fallos de navegador en cadena.
- [x] Composición compacta bajo 400 px, conservando tipografía y áreas táctiles de 44 px. Regresión con dos familias tipográficas y límites 320/359/360/390/399/400/600.
- [x] 203 Django sin omisiones, 9 Node y 85 Chromium en Linux correctos; check/Ruff/migraciones/diff correctos. Regresión probada antes/después y también en Windows.
- [x] Guía para la carpeta local Raspberry y Portainer: respaldos, ensayo de restauración/migraciones, reconstrucción y recreación de web con volúmenes existentes.

Publicación y CI remoto se comprueban después del commit/push; el resultado se informa en la conversación con su hash y enlace. No hay migraciones nuevas por esta corrección. No se accedió a Raspberry ni se cambió Portainer.


## Despliegue Raspberry autorizado y verificado - 18/10/2026

- [x] Inspeccion del stack real dulce-salado y checkout source; variables de Portainer, imagen local, puerto 8003 y binds conservados.
- [x] Imagen ARM64 construida; 203 Django OK en base aislada (16 inspecciones PDF omitidas por ausencia de Poppler en runtime). CI funcional previo completo aprobado.
- [x] Respaldo PostgreSQL/media/configuracion, copia fuera de la Raspberry, restauracion y ensayo de 0005-0009 verificados antes de migrar datos reales.
- [x] 45 productos, 1 usuario y 45 fotos conservados; solo 21 incrementos y 4 productos con centavos cambian conforme a las migraciones.
- [x] Web actualizado por Portainer; 13 contenedores restantes, incluido PostgreSQL, conservan IDs, imagenes, tiempos de inicio y reinicios.
- [x] Navegador real: 320/390/768/1280, axe, fotos, cantidades, totales, revision/copiar/URL WhatsApp interceptada y Admin login correctos; sin errores JS ni respuestas 500.

El registro documental se incorpora a main y a la imagen final; no cambia funcionalidad ni datos. Detalles operativos y respaldo en ACTUALIZAR_RASPBERRY_PORTAINER.md. No se requiere ninguna accion manual del propietario para completar este despliegue.

## Solicitudes persistidas autorizadas — 18/10/2026

- [x] Order/0010: instantánea, token privado, código PostgreSQL e idempotencia concurrente.
- [x] Formulario de cliente/entrega, detalle privado y resultado/reenvío normal e iframe.
- [x] 220 pruebas Django y 9 Node correctas; 14 escenarios nuevos Chromium correctos a cuatro anchos.
- [x] Regresión Chromium completa: 84 pruebas, sin fallos ni omisiones.
- [x] Publicación main 623d130 y CI success 39168319212.
- [x] Respaldo/restauración, ensayo con pedido histórico y renovación de 45 demos con fotos originales conservadas.
- [x] Migración real 0010 y actualización sólo web, preservando otros 13 contenedores.
- [ ] Corrección de tipo MIME WebP detectada en Raspberry y prueba funcional real final.
- [ ] Dominio HTTPS público futuro; actualmente prueba local expresamente autorizada.
