# Estado de ejecución — MVP

Fecha de inicio: 2026-10-10. Trabajo autorizado secuencial en `main` hasta completar el MVP.

## Tarea actual
CORRECCIONES VISUALES COMPLETADAS Y PUBLICADAS. Cuatro ajustes y QA final verificados: 63 Django, 7 Node y 22 Chromium, checks/Ruff/migraciones OK. CI success de la QA final run 38105183767. Historial previo y datos comerciales conservados; próximo paso, pruebas locales del dueño según README/QA.

## Decisiones autorizadas
- kg, unidad y paquete; incrementos iniciales 0,1 kg y 1 unidad/paquete. Sin conversión de gramos.
- Mayorista opcional y manual; minorista por defecto. ARS con Decimal y dos decimales.
- WhatsApp por entorno, sin número real inventado ni datos comerciales de ejemplo.
- Admin: usuario activo staff con permisos; superusuario inicial para el dueño.

## Finalizado y pendiente
- Lectura completa de AGENTS, README, especificación, arquitectura, UX y roadmap.
- Auditoría finalizada: clave obligatoria, tests Admin, documentación y exclusiones Docker.
- Modelos y Admin finalizados: precios no negativos, incrementos válidos, categorías protegidas contra borrado con productos, permisos por modelo.
- Imágenes finalizadas: JPEG/PNG/WebP reales hasta 5 MB, 6000 px/lado y 16 MP; WebP hasta 1200 px sin metadata; nombres UUID y limpieza al reemplazar/quitar/borrar tras commit.
- Catálogo finalizado: búsqueda nombre/marca, categorías activas, paginación de 24, estados vacíos, formato ARS, templates escapados y CSS mobile-first.
- Carrito finalizado: localStorage guarda ID/cantidad/tarifa, unidad y hash de revisión, nunca importes; refresco POST con CSRF devuelve HTML y calcula Decimal. Cantidades/selección editables, quitar/vaciar, persistencia y sincronización entre pestañas.
- Cambios de precio informados; mayorista ausente, producto retirado o cambio de unidad bloquean total hasta corregir. Durante consultas/fallos no se muestran totales anteriores.
- WhatsApp finalizado: diálogo nativo, aviso exacto, cancelar/continuar, mensaje completo y copiable. Última validación al continuar; si cambió catálogo exige nueva revisión. Número opcional por entorno; sin configurar no navega.
- QA final, instrucciones locales, publicación y CI completados. Configuración comercial y prueba de teléfono real a cargo del dueño, según QA.md.

## Archivos de la tarea
Auditoría: configuración, tests core, Docker ignores y documentación. Modelos: `catalog/models.py`, `catalog/admin.py`, `catalog/apps.py`, `catalog/tests.py`, `catalog/migrations/0001_initial.py`, settings y especificación.

## Validaciones reales
- Git limpio, rama main; fetch origin/main ejecutado.
- Docker Desktop disponible mediante ejecución con permisos de herramienta.
- CI ya define DJANGO_SECRET_KEY de prueba; resta verificar ejecución tras publicación.
- Docker Python 3.12/PostgreSQL: check sin errores, 7 tests OK, Ruff OK, migraciones base aplicadas, makemigrations --check sin cambios.
- `.env` y `.env.local` ignorados; `.env.example` conservado. Claves locales generadas y no versionadas.
- Modelos en Docker: 15 tests OK, check/Ruff OK, migración 0001 aplicada y sin cambios pendientes.
- Imágenes en Docker: 20 tests OK, check OK, Ruff corrigió un orden de imports y queda limpio; migración 0002 aplicada y sin cambios pendientes. Archivos: images/signals/test_images, models/apps, urls, requirements y migración 0002.
- Pillow añadido por necesidad de ImageField y optimización WebP; sin servicios adicionales.
- Catálogo en Docker: 27 tests OK, check/Ruff OK y sin migraciones pendientes. Archivos: views, templatetags, test_views, templates base/home, CSS, rutas y test core. Se retiró la vista temporal.
- Herramienta de navegador: no hay superficies disponibles (inventario vacío); QA visual pendiente en fase 6. Colores provisionales, sin logo original disponible.
- Carrito en Docker: 34 tests Django OK, 4 tests Node OK, check/Ruff OK y sin migraciones pendientes. CI ampliada a migraciones/Node. Archivos: cart.py, vistas/rutas, templates, JS cart-core/cart, CSS, tests y CI.
- WhatsApp en Docker: 39 tests Django OK, 4 Node OK, check/Ruff OK y sin migraciones pendientes. Tests verifican texto completo codificado, marcas opcionales, redondeo y cambios antes de salida. No se envió ningún mensaje ni se visitó un teléfono de prueba.
- Archivos fase 5: whatsapp.py/test_whatsapp.py, vistas/rutas/settings, .env.example, templates carrito/revisión, JS y CSS.
- QA final: 42 tests Django, 4 Node y 11 comprobaciones Chromium OK; checks/Ruff OK y sin migraciones pendientes. Cero infracciones axe en vistas verificadas. Capturas 360/390/430/1280 px inspeccionadas, sin scroll horizontal y controles de 44 px.
- Base comercial comprobada vacía. Servidor QA detenido y base descartable eliminada (consulta de nombres QA sin filas). WhatsApp interceptado, sin envío.
- Correcciones QA: contraste y contenedor de imágenes; foco inicial en título para leer el aviso; cancelar durante la revalidación invalida la respuesta pendiente; ocultar importes ante almacenamiento inválido. Tests extra de orientación/metadata/transparencia y suma de subtotales redondeados.
- Archivos fase 6: tests/browser_server.py y browser.spec.cjs, test_images/test_cart, CSS/JS/template revisión, README, QA/arquitectura/estado/roadmap y workflow. Playwright 1.64.0/axe 4.13.0 sólo para desarrollo en .qa ignorado por Git/Docker.
- Imagen Docker final reconstruida y servicios web/db levantados; migrate sin pendientes y check OK. HTTP catálogo/carrito 200. Main y origin/main sincronizados, sin archivos locales sensibles en Git.
- CI ampliada completada con success: `https://github.com/fitksh/Dulce-Salado/actions/runs/38086302160`, commit `abc3727adba1664856877541c540146949da272c`. Todos los pasos, incluido QA de navegador, correctos.

## Publicación
Último commit funcional publicado y verificado: `abc3727adba1664856877541c540146949da272c` (QA final), CI success run `38086302160`. WhatsApp `14e1863`: CI success run `38085641568`; carrito `8a904e7`: CI success run `38085464137`; catálogo `1486025`: CI success run `38085214330`; imágenes `a639373`: CI success run `38084993979`; modelos `1813f7b`: CI success run `38084873987`; auditoría `50ef9b0`: CI success run `38084761552`.

El cierre documental es el commit que contiene este estado. Su identificador exacto se obtiene con `git log -1 --format=%H`; su run CI se consulta en GitHub Actions. No se intenta incluir el hash de un commit dentro de sí mismo.

## Bloqueos
Ninguno de implementación. El número real de WhatsApp deberá configurarlo el dueño.

## Próxima tarea exacta
El dueño configura WHATSAPP_PHONE en .env, crea su administrador y carga categorías/productos reales siguiendo README. Luego prueba carrito/WhatsApp en su teléfono y lector de pantalla según QA.md. No hay tareas de implementación pendientes del MVP; no avanzar a despliegue sin nueva autorización.

## Nueva etapa UX/UI — 2026-10-10

Solicitud complementaria leída completa junto a los documentos/código/tests actuales. Base main sincronizada; checks/Ruff iniciales OK. El MVP anterior se conserva como historial.

Tarea actual: 1, identidad/navegación. Archivos: base/home/cart templates, CSS, tests de vistas/navegador, logo WebP y script de conversión, documentación. Fuente provista `assets/brand/logo-dulce-salado.jpg` (nombre distinto al previsto); se conserva y convierte con Pillow existente, sin recortes ni ampliación.

Tarea 1 validada: logo WebP 150 × 150 (5874 bytes), check/Ruff OK, 15 tests Django afectados OK, sin migraciones pendientes y 11 comprobaciones Chromium OK. Captura móvil inspeccionada; header en una fila a 360/390/430/1280 px y axe sin infracciones. Fuente original conservada.

Pendientes: tareas 2–7. Último commit previo: `dfd2bac`, CI success run `38086451969`. Sin bloqueos conocidos. Próxima acción: publicar tarea 1, verificar CI y continuar con catálogo/controles.

Tarea 1 publicada: `6a2389f`, CI success run `38093591790`.

Tarea 2 validada: búsqueda ORM nombre/marca/descripción priorizada, selector GET móvil bajo 800 px conservando búsqueda, stepper compartido y aritmética exacta, condición específica discreta y placeholder estable. Archivos: views/test_views, templates home/cart_contents/include/base, CSS, JS cart-core/quantity/cart, tests Node/navegador y especificación/UX. Check/Ruff OK, sin migraciones pendientes, 17 tests Django afectados, 5 Node y 12 comprobaciones Chromium OK (incluye filtro sin JavaScript y steppers en ambas vistas). Responsive 360/390/430/1280 px y axe OK.

Pendientes: tareas 3–7. Próxima acción: publicar tarea 2 y verificar CI; corregir scroll y estandarizar feedback.

Tarea 2 publicada: `c8fbf08`, CI success run `38093785080`.

Tarea 3 validada: se reprodujo desaparición del control en carrito largo antes del arreglo. Refresh conserva layout, controles del mismo producto/unidad, foco y scroll; importes ocultos hasta revalidar, serial de concurrencia y localStorage conservados. Feedback verde breve con enlace junto al producto, estilos reutilizables/roles y avisos semánticos. Admin nativo comprobado con creación/edición de ambos modelos, sin sistema paralelo ni cambios visuales. Archivos: cart.js/CSS, templates home/cart/cart_contents/cart_review, catalog/tests, QA fixtures/browser, UX/roadmap/estado. Check/Ruff OK, sin migraciones, 22 tests Django afectados, 5 Node y 13 Chromium OK. Sin envíos reales de WhatsApp.

Pendientes: tareas 4–7. Próxima acción: publicar tarea 3, verificar CI y agregar exportación CSV.

Tarea 3 publicada: `460fb26`, CI success run `38094129519`.

Tarea 4 validada: Exportar CSV visible en listado Admin también para permiso sólo de lectura; requiere staff y ver/cambiar producto. Reutiliza queryset de ChangeList sin paginar, incluidos productos inactivos y filtros/búsqueda. CSV estándar UTF-8 BOM, punto y coma, coma decimal, diez columnas solicitadas y prefijo protector de fórmulas en textos. Archivos: catalog/admin.py y test_csv.py, template Admin, browser test y docs. Check/Ruff OK, sin migraciones; 13 tests Django afectados OK y 14 Chromium OK, incluida descarga filtrada. Ninguna dependencia nueva.

Pendientes: tareas 5–7. Próxima acción: publicar tarea 4, verificar CI y agregar configuración comercial/Cómo llegar.

Tarea 4 publicada: `7f68a38`, CI success run `38094267809`.

Tarea 5 validada: BusinessSettings único por PK 1 y constraint; Admin impide segunda alta/borrado y respeta permisos. Dirección opcional y URL HTTPS de Maps validada; /como-llegar/ enlazado desde footer, sin indicaciones si falta dirección. Sin API key, iframe ni dependencias; URL de búsqueda codificada según documentación oficial de Google. Archivos: models/admin/views, config/urls, template directions/base, CSS, migración 0003_business_settings, test_business/browser y docs. Check/Ruff OK, 23 tests Django afectados y 15 Chromium OK; sin migraciones pendientes, 0003 aplicada localmente. Capturas 360/390/430/1280 px y axe OK. La dirección QA existe sólo en base descartable, nunca en la comercial.

Pendientes: tareas 6–7. Próxima acción: publicar tarea 5, verificar CI y agregar horarios semanales.

Tarea 5 publicada: `82b2d57`, CI success run `38094437168`.

Tarea 6 validada: OpeningInterval es el único modelo adicional a la configuración central. Horario semanal se inicializa mediante «publicar horario semanal», falso por defecto; borradores no se publican. Validación de día/orden de horas y superposiciones, incluido conjunto final editado/borrado en inline Admin. Día sin intervalos cerrado sólo con semana publicada. Estado/server y reloj JS usan America/Argentina/Buenos_Aires; actualiza cada 15 segundos y al volver a pestaña, sin fetch periódico. Details nativo debajo del header, verde/neutro con texto y aviso de horarios publicados. Archivos: models/admin/business/context_processors/views, settings, migración 0004_opening_hours, include/base/CSS/JS, tests Django/Node/browser y docs. Check/Ruff OK, sin migraciones pendientes; 33 tests afectados, 7 Node y 16 Chromium OK. Se verificaron dos intervalos en navegador, tres en backend, edición/borrado, cambio de hora sin peticiones, teclado y details sin JavaScript. Capturas 360/390/430/1280 px y axe OK; 0004 aplicada sin poblar la base comercial.

Pendiente: tarea 7. Próxima acción: publicar tarea 6, verificar CI y ejecutar QA final/documentación.

Tarea 6 publicada: `7f2b025`, CI success run `38094790574`.

Tarea 7, QA local: 60 tests Django completos, 7 Node y 16 Chromium OK; check/Ruff OK, sin migraciones pendientes. Responsive 360/390/430/1280 px, capturas de catálogo/Cómo llegar/horarios y axe sin infracciones. Regresión ampliada de scroll/foco, teclado, respuestas fuera de orden y fallo de red con contenido existente. Se corrigió el montaje del refresco para mantener conectado el contenedor de controles: mover inputs enfocados disparaba blur/change nativo adicional. Se espera fin de interceptaciones en el test antes de retirarlas. Horario sólo anuncia cambios. Archivos finales: cart.js/business-hours.js, cart_contents, browser test, README/QA/roadmap/estado. Sin cambios en cálculo de precios, formato WhatsApp, esquema localStorage o infraestructura.

Pendiente: publicar QA/correcciones finales, verificar CI y cerrar estado/roadmap. Datos reales de dirección/horarios/WhatsApp y pruebas de teléfono/lector/Excel a cargo del dueño; no bloquean implementación.

## Cierre de la etapa complementaria

QA/correcciones finales publicadas: `61d5e52a22416999e1d6f387cca3c9012a69458c`, [CI success run 38095362239](https://github.com/fitksh/Dulce-Salado/actions/runs/38095362239). Todos los pasos ejecutados correctamente, incluida suite de navegador.

Entorno local reconstruido con docker compose up --build -d; migrate sin pendientes y check OK. HTTP catálogo/carrito/Cómo llegar 200. Servidor QA detenido y consulta de bases QA sin filas. Capturas finales inspeccionadas a 360/390/430/1280 px y confirmación verde con Ver carrito. Regresión incluye retorno de foco a revisión tras Escape. No se modificaron módulos de cálculo/WhatsApp, esquema localStorage, Docker o workflow fuera del alcance.

Verificación local de configuración (sin exponer valores): dirección y enlace exacto Maps presentes, horario semanal publicado con 12 intervalos, WHATSAPP_PHONE configurado. Los datos existentes se conservan. Revisar su exactitud y validar teléfono/lector/CSV Excel según QA.md. No quedan tareas de implementación de esta etapa ni bloqueos conocidos.

Este commit sólo cierra documentación y roadmap. Su hash se obtiene con git log -1 --format=%H y su CI se verifica al publicarlo; no se incrusta el identificador de un commit dentro de sí mismo.

Corrección de CI: run 38095501842 (commit documental 8fffa5b) falló intermitentemente en el test de foco tras Escape. Se comprobaba el botón antes de finalizar el refresh del evento close; los escenarios dependientes luego agotaban su espera. Se hace explícito el foco al botón de revisión antes de refrescar y el test espera la respuesta y foco recuperado. Verificada localmente: 13 tests Django afectados, check/Ruff/migraciones y 16 Chromium OK. Pendiente verificar la corrección en CI; las suites Django/Node/migraciones/lint del run anterior pasaron.

Corrección publicada y verificada: `95e79262507aff4b718690161d3f1dca30e91fb4`, [CI success run 38095823292](https://github.com/fitksh/Dulce-Salado/actions/runs/38095823292). Suite completa de CI correcta (60 Django, 7 Node, 16 Chromium, checks/Ruff y migraciones). Entorno local reconstruido nuevamente, check OK y migrate sin pendientes. Servidor/base QA descartados. El fallo anterior queda como historial; no quedan correcciones de implementación pendientes. Este cierre documental registra el último resultado funcional conocido; el hash y CI del propio commit de documentación se consultan en Git/GitHub.

## Segunda iteración UX/UI — 2026-10-10

Solicitud leída completa; documentos obligatorios, templates, CSS, JS y pruebas revisados. Main limpio y sincronizado con origin/main antes de editar. Autorizados siete cambios secuenciales, commits y publicación sin nuevas dependencias/modelos/migraciones. Se conservan datos comerciales y reglas de negocio.

Tarea 1 implementada, pendiente validación: horarios dentro del header con details flotante, cierre exterior/Escape y foco; textos solicitados eliminados; h1 Nuestros productos, búsqueda etiquetada sin texto visible; categorías auto-submit con fallback GET; icono ubicación, footer centrado y toolbar móvil apilada. Archivos: templates base/home/cart/directions/business_hours, CSS, JS catalog/business-hours y tests vistas/horarios/navegador. Criterios: filtros y horarios intactos, teclado/sin JS, panel sin desplazar contenido, cinco anchuras sin overflow. Pendientes tareas 2–7.

Tarea 1 validación backend: check/Ruff OK, 28 pruebas Django afectadas y 7 Node OK, makemigrations sin cambios. QA de navegador ampliado a 360/390/430/768/1280 px, sin desbordamiento, categorías automáticas/fallback y toolbar simétrica; panel dentro de header (<150 px), no desplaza main, Escape con retorno de foco y cierre exterior. Captura móvil inspeccionada. Se corrigió el test exterior para pulsar un texto del footer fuera del panel (el h1 estaba detrás de éste). Resultado Chromium se registra antes de publicar.

Tarea 1 Chromium final: 16 comprobaciones OK, axe sin infracciones y cinco anchuras verificadas. Próxima acción: publicar/verificar CI; luego tarea 2, mapa fijo del propietario sin depender de conectividad externa.

Tarea 1 publicada: b503ac4cf6f4ef924e3e6a61917b22b48ae5be02, CI success run 38099439417.

Tarea 2: iframe fijo exacto proporcionado por el dueño en Cómo llegar, visible también en móvil, altura responsive, title/lazy/referrerpolicy/allowfullscreen. Dirección y enlace Admin preservados, incluso cuando falla el recurso externo. El iframe del comercio es independiente de la dirección editable y deberá actualizarse manualmente en templates/directions.html si el comercio se muda. Sin modelos/dependencias/migraciones. Archivos: directions/CSS, test_business y browser (Maps interceptado). Criterios: cinco anchuras, atributos correctos, fallback dirección/botón funcionando sin red Google.

Tarea 2 backend: 15 pruebas Django afectadas, check/Ruff y control de migraciones OK. QA intercepta el iframe (o aborta en contexto sin JS), sin depender de Google. Se hizo explícita la espera de navegación y mejora progresiva del selector en el test; evita seleccionar en el DOM anterior mientras termina la búsqueda. Sin cambios en búsqueda/categorías.

Tarea 2 validada: 16 Chromium OK, iframe visible/medidas/atributos correctos a 360/390/430/768/1280 px, axe OK y navegación externa interceptada. Captura móvil inspeccionada. Próxima acción: publicar/verificar CI; luego dialog de imagen única.

Tarea 2 publicada: bae066f169fca439267bfdb07e7258dd772d2dac, CI success run 38099651165.

Tarea 3 implementada: único dialog en catálogo, foto original optimizada sin variantes/recorte, botón Cerrar, Escape/fondo y foco al disparador. Sólo las fotos tienen enlace; sin JS el enlace permite ver el archivo existente. Placeholder intacto. Archivos: home/catalog.js/CSS y test_views/browser. Criterios: teclado, foco, responsive cinco anchuras, axe y recurso único. Pendiente validación/publicación.

Tarea 3 validada: 10 Django afectados y 17 Chromium OK, check/Ruff/migraciones OK. Apertura Enter/clic, cierre botón/Escape/fondo, mismo archivo y retorno de foco; cinco anchuras sin overflow y axe OK. Captura ampliada inspeccionada. Publicar/verificar CI antes del destacado mayorista.

Tarea 3 publicada: 3afb227a1af580c6d417991a9f7c239a8661707a, CI success run 38099815624.

Tarea 4: destacado moderado rosa #fff0f6 con texto #68384c, sin cambios de selección o condiciones. Archivos: CSS, test_cart y browser; tests comprueban sólo condición específica, ausencia cuando vacío y selección mayorista manual. Criterios: contraste axe, responsive y no texto genérico añadido.

Tarea 4 validada: 24 pruebas Django afectadas, 17 Chromium, check/Ruff y migraciones OK. Axe sin infracciones de contraste; cinco anchuras. Captura carrito móvil inspeccionada, condición suave y toolbar de igual ancho. Condición vacía/retail no muestran bloque; sin aplicación automática. Próxima acción: publicar/verificar CI, luego notificaciones flotantes.

Tarea 4 publicada: 8570e2314554cd900432641d53e78d9d620b654d, CI success run 38099976282.

Tarea 5 en curso: función Notifications.show única con plantilla reutilizable, fijo superior/safe-area, cuatro estilos, reemplazo sin acumulación, cierre manual y temporizadores 5/8 segundos pausables por puntero/foco. Dos ubicaciones del mismo componente (página y diálogo modal) para mantener acciones operables dentro del modal; sólo una visible/anuncia a la vez. Éxitos inline eliminados; campos/productos/almacenamiento/red mantienen explicaciones persistentes sin roles live duplicados. Archivos: base/home/cart/cart_contents/cart_review/quantity_control/notification, JS notifications/cart/quantity, CSS y tests de navegador. Criterios: visible tras scroll, foco/scroll intactos, pausa/cierre/duración y bloqueos persisten.

Tarea 5 validada: 24 Django afectados, 7 Node, 18 Chromium OK; check/Ruff/migraciones OK. Tests verifican aviso tras scroll >2000 px, foco/scroll sin cambio, cinco anchuras, éxito con Ver carrito, incompatibilidad de tarifa visible, reemplazo sin acumulación, pausa de 10 s con acción enfocada, duración 5/8 s, cierre manual y error persistente tras desaparecer el aviso que mantiene revisión bloqueada/total ausente. Axe OK, captura error flotante inspeccionada. Se eliminó comparación frágil de saltos de línea en prueba, comprobando el mensaje semántico. Publicar/verificar CI antes de WhatsApp.

Tarea 5 publicada: 278790f70b80842341d7affaca95174c08812026, CI success run 38100310749.

Tarea 6 implementada: apertura about:blank síncrona desde clic, opener null inmediato y meta referrer no-referrer; se conserva handle para cerrar ante cambios/errores/cancelación. Sólo tras respuesta vigente se navega el contexto nuevo. Fallback validado target blank/noopener/noreferrer visible; no se reemplaza pestaña ni se borra carrito. Visibilidad no interrumpe la verificación en curso. Archivos: cart.js/cart_review, tests WhatsApp/browser. Criterios: revalidación y aviso íntegros, popup/contexto/fallback/cancelación con destinos interceptados, sin envío real. Referencias técnicas: https://html.spec.whatwg.org/multipage/nav-history-apis.html y https://developer.mozilla.org/en-US/docs/Web/API/Window/open.

Tarea 6 validada: 14 Django afectados, 7 Node y 20 Chromium OK; check/Ruff/control de migraciones OK. Contexto nuevo con opener null/referrer vacío, pestaña/carrito originales intactos; popup bloqueado abre enlace manual seguro; cambios de precio/cancelación/red cierran provisional sin navegar. QA espera el evento close real, no un total que ya estaba visible. Error de conexión de WhatsApp informado en español. Aviso obligatorio y texto completo preservados. Publicar/verificar CI antes de QA final.

Tarea 6 publicada: 76babad791bc2e08103e9c0fb7e57f0a117ab4dd, CI success run 38100657041.

Tarea 7 en curso: regresiones adicionales de Instagram en pestaña nueva, cantidad nativa inválida, copia del mensaje con éxito/fallback y carrito cambiado en otra pestaña durante validación final. El aviso de copia se centraliza en Notifications.show manteniendo textarea y botón. Archivos: cart.js/tests browser, README y docs arquitectura/especificación/UX/QA/roadmap/estado. Criterios: suite completa, cinco anchuras, axe, entorno actualizado y publicación/CI final verificadas.

Tarea 7 QA completa: 63 Django, 7 Node, 22 Chromium OK, check/Ruff y makemigrations sin cambios. Axe sin infracciones; cinco anchuras verificadas. Instagram/Maps/WhatsApp interceptados sin navegación real/envíos; prueba de copia success/fallback dentro de modal y cambio de storage durante validación cierran provisional sin destino. README/especificación/arquitectura/UX/QA actualizados, historial previo conservado. Se amplían capturas de viewport/foto/toolbar para inspección final, con regresión responsive de alineación exacta a tarjetas. Pendiente última revisión visual, publicar/verificar CI y actualizar entorno local.

Última verificación local: 22 Chromium OK tras ampliar capturas y comprobaciones de toolbar. Capturas inspeccionadas de catálogo móvil/tablet/escritorio, foto móvil, avisos éxito/error, carrito, dirección y horarios. Sin overflow/recortes inesperados. Entorno Docker reconstruido, migrate sin pendientes y check OK; HTTP 200 en /, /carrito/ y /como-llegar/. QA detenido y bases descartables consultadas sin filas. Configuración real verificada sólo por presencia (sin revelar valores): dirección/enlace Maps, 12 intervalos publicados y teléfono presentes; ningún dato comercial sobrescrito. Pendiente publicación y CI final.

## Cierre de la segunda iteración UX/UI

Tarea 7 publicada: a43a5789feafa1966362d6f0950beafab779f7f4, [CI success run 38101095717](https://github.com/fitksh/Dulce-Salado/actions/runs/38101095717). Suite completa correcta: 63 Django, 7 Node y 22 Chromium, check/Ruff y migraciones. Tareas 1–6 también con CI success, detalladas arriba.

Todas las mejoras solicitadas completas; sin bloqueos de implementación ni fallos conocidos de pruebas. Sin dependencias/modelos/migraciones nuevos, cálculo y datos comerciales conservados. Entorno local actualizado, tres vistas 200, QA descartado, capturas inspeccionadas y main sincronizada. Próximo paso concreto: dueño prueba en teléfono real filtros, horarios flotantes, fotos, avisos y apertura/retorno WhatsApp; valida datos/iframe externo y lectores, siguiendo README/QA. Infraestructura futura fuera de esta tarea.

Este cierre documental marca roadmap y estado reales. Su hash y CI propios se consultan en Git/GitHub después de publicar; el run anterior verifica el último cambio funcional completo y no se incrusta el hash de un commit dentro de sí mismo.

QA adicional posterior al cierre: CI documental 7220c8e success run 38101221498. Se reprodujo en lectura local que un clic dentro del iframe Maps mantenía abierto el panel horario (activeElement IFRAME); estos eventos no se propagan al documento padre. Corrección mínima en business-hours.js: al perder foco hacia un iframe, cerrar details sin mover foco. Regresión añadida al escenario horario. Pendiente validar/publicar corrección y CI; no cambia horarios/datos/modelos.

Corrección adicional validada: al tocar el mapa el panel se cierra y el foco permanece en IFRAME. 6 Django afectados, 7 Node y 22 Chromium OK; check/Ruff/migraciones OK. La suite completa previa de 63 Django y CI documental permanecen como evidencia histórica; CI de esta revisión ejecuta nuevamente la suite completa al publicar. El ajuste está incluido en el mismo alcance, sin pendientes de implementación. El hash/run propios se consultan en Git/GitHub después de publicar.

## Correcciones visuales puntuales — 2026-10-10

Nueva solicitud: cuatro ajustes visuales y QA secuencial; main limpia, fetch/pull --ff-only sin cambios antes de editar. No se modifican reglas, modelos, datos comerciales ni dependencias.

Tarea 1 validada: Grid dejaba crecer la fila automática por el tamaño intrínseco del enlace/imagen. Marco de 210 px frente a enlace vertical de 716 px en 1280; overflow ocultaba la fotografía pese a contain. Flex con altura definida mantiene marco/enlace/imagen en 210 px. Fotos horizontales 600×400, cuadradas 400×400 y verticales 300×600 con bordes/esquinas QA muestran cuatro bordes completos, centrados y sin deformación en cinco anchuras. Dialog sólo muestra imagen y ×, con nombre/descripción accesibles ocultos, Escape/fondo/foco y enlace nativo sin JS. WebP/almacenamiento originales intactos.

Archivos: home.html, site.css, catalog.js, test_views.py, browser_server.py/browser.spec.cjs y documentación. 10 Django afectados y 22 Chromium correctos, Ruff OK; axe sin infracciones y capturas de miniaturas/modal inspeccionadas. El test sin JS comprueba la petición de navegación nativa: el tipo MIME del entorno puede mostrar o descargar el archivo. QA reiniciado para recargar templates cacheados y fixtures; no toca base comercial. Próxima acción: publicar/verificar CI y reorganizar header.

Tarea 2 validada: base integra horarios entre marca y carrito dentro de header-inner; Grid de tres columnas desde 800 px, una columna centrada bajo ese ancho. Panel centrado respecto al summary, ancho limitado al viewport; no cambia posición de main. 16 Django afectados, 7 Node, 22 Chromium y check OK; capturas móvil/escritorio y horarios abiertos inspeccionadas, axe sin infracciones. Cierre control/Escape/exterior/iframe y foco siguen correctos; sin cambios de cálculo/modelos/Admin. Archivos: base.html, business_hours.html, site.css y pruebas de navegador. Próxima acción: publicar/verificar CI y unificar Cómo llegar.

Tarea 1 publicada: e43bebde6b75acba692bbb0c364f70536716da47; CI success run 38104627303. Tarea 2 publicada: 59d86fff083a5934235c9b5000b2119609939619; resultado CI se registra al confirmarlo.

Tarea 3 validada: una business-card integra encabezado principal Dirección, address/botón desde Admin y mismo iframe. Dos columnas desde 800 px, mapa con dos tercios; una columna por debajo. URL/title/lazy/referrerpolicy/allowfullscreen exactos, sin configuración comercial nueva. Ausencia de dirección sigue sin enlace falso. 16 Django afectados, 22 Chromium y Ruff OK; axe en cinco anchuras, capturas móvil/escritorio inspeccionadas y clic dentro del iframe de QA funcionando. Navegación Maps existente interceptada. Archivos: directions.html/site.css, test_business.py/browser.spec.cjs y documentación. Próxima acción: publicar/verificar CI y centrar footer.

Tarea 2 CI success confirmada: run 38104718180, commit 59d86ff. Tarea 3 publicada: 3566883dc5f83e342ae0416f0e6e989f63b39aac; CI run 38104812406 en ejecución al iniciar footer.

Tarea 4 validada: centrado base de site-footer y footer-links para todas las resoluciones; retiradas las reglas redundantes sólo móviles. Textos, iconos y destinos intactos. Tests geométricos comprueban grupo de enlaces centrado, ambos SVG y alturas ≥44 px; Instagram mantiene pestaña nueva/opener null/referrer vacío y Cómo llegar su ruta. 10 Django afectados y 22 Chromium OK; capturas footer en 360/390/430/768/1280 inspeccionadas, axe sin infracciones. Archivos: site.css, browser.spec.cjs y documentación. Próxima acción: publicar/verificar CI y QA final completa.

Tarea 3 CI success: run 38104812406, commit 3566883. Tarea 4 publicada: e9ced7e1f44d5c4fddde4649a085a84f7fd2f252; CI success run 38104891571. Las cuatro tareas tienen CI completa correcta.

Tarea 5 QA final: 63 Django, 7 Node y 22 Chromium correctos, check/Ruff OK y makemigrations sin cambios. Se amplía QA a tres proporciones también dentro del modal (15 capturas) y al límite 800 px del header; axe también en cada ancho de horarios. Capturas de fotos/modal/header/horarios/dirección/footer inspeccionadas; sin recortes ni overflow. Regresión completa del carrito, CSV, Admin y WhatsApp conservada, sin modificar su código.

Entorno Docker local reconstruido y check OK; /, /carrito/ y /como-llegar/ responden 200. Inspección comercial sólo lectura: 6 productos, 3 categorías, dirección/enlace/WhatsApp presentes y 12 intervalos publicados. Fotos reales 675×1200 y 900×1200 completas; marco/enlace/imagen 210 px. Axe del catálogo real sin infracciones a cinco anchuras. Horarios reales: main inmóvil en todas, header 165 px móvil, 183 px tablet y 93 px desktop.

La primera captura Maps estaba bloqueada por el sandbox (ERR_NETWORK_ACCESS_DENIED). Verificación de red autorizada en lectura: iframe HTTP 200 y mapa real visible en capturas live-directions, conservando URL/políticas. Capturas reales inspeccionadas móvil/escritorio y despliegue de horarios. No se alteró información comercial, no se enviaron mensajes ni se agregaron artículos al carrito comercial. QA detenido y consulta de bases descartables sin filas. Pendiente publicar la ampliación QA/documentación y confirmar su CI para cerrar estado/roadmap.

## Cierre de correcciones visuales puntuales

Tarea 5 publicada: 69902fb54e4ba55c239a66181c95bc41f251bd6a; [CI success run 38105183767](https://github.com/fitksh/Dulce-Salado/actions/runs/38105183767), incluida suite completa y capturas. Tareas 1–4 también success, registradas arriba. Las cinco tareas completas; sin fallos conocidos de implementación ni cambios fuera de alcance.

Archivos modificados en esta iteración: templates/home.html, base.html, directions.html e includes/business_hours.html; static/css/site.css y static/js/catalog.js; catalog/test_views.py y test_business.py; tests/browser_server.py y browser.spec.cjs; README.md y docs/ARCHITECTURE.md, UX_UI.md, ROADMAP.md, EXECUTION_STATUS.md y QA.md. No se modificaron modelos, migraciones, procesamiento de imágenes, carrito, WhatsApp, notificaciones, CSV, Admin, Docker ni datos comerciales.

Entorno local actualizado y disponible; main sincronizada. Próximo paso concreto: recargar localhost:8000 con Ctrl+F5, comprobar fotos completas/ampliación, header/horarios, dirección/mapa y footer en teléfono real; mantener pruebas manuales de lector/retorno de aplicaciones externas descritas en QA. Este commit cierra sólo documentación; su propio hash y CI se consultan en Git/GitHub después de publicar.

Verificación de cierre documental: 144e0791a6695b0a2eb9d18bc28c2a6c06a5fa3b, CI success run 38105345534.

QA adicional de orientación horizontal: a 844×300 el modal conservaba altura de foto 75dvh más padding; imagen terminaba en y=297 frente al borde del dialog y=285. Ajuste mínimo en site.css: limitar además a 90dvh menos 5rem para reservar cierre/padding. A 844×300 ahora no hay scroll interno y la foto completa termina antes del borde; capturas 300/390 de alto inspeccionadas. Regresión añadida a browser.spec.cjs. 10 Django afectados, 7 Node y 22 Chromium correctos, check/Ruff/migraciones OK; la suite completa previa de 63 Django y sus CI están registradas arriba. CI de este último ajuste repite suite completa; hash/run propios se consultan después de publicar. Ningún otro comportamiento cambiado.

## Nueva iteración UX/UI y datos de prueba — 2026-10-11

Tarea 1 validada: logo CSS de 64 px sin modificar el archivo; navegación Catálogo/Carrito agrupada con aria-current y columnas equilibradas. Marca, horarios y acciones en fila desde 800 px y tres regiones centradas en móvil. Separadores únicamente entre los siete días. 11 Django afectados, 22 Chromium y Ruff correctos; cinco anchuras más límite 800 px, axe y capturas móvil/escritorio inspeccionadas. Archivos: base.html, site.css, test_views.py y browser.spec.cjs. Datos y horarios conservados. Próxima tarea: Ubicación y redirección permanente.

Tarea 1 publicada: 35b186067cc994b74d3ed399b5dc0b2acc079f8a; CI success 38114948120.

Tarea 2 validada: /ubicacion/ utiliza la vista existente; /como-llegar/ redirige 301. Texto Ubicación y columna informativa centrada; dirección exclusivamente Admin, iframe exacto intacto. 18 Django y 22 Chromium correctos; redirección, cinco anchuras, axe y captura móvil inspeccionada. Se corrigieron los selectores de pruebas que aún buscaban los textos anteriores. README/spec/UX actualizados sin modificar datos. Próxima tarea: simplificar carrito y reutilizar visor de fotos.

Tarea 3 validada: título oculto accesible y toolbar retirado; Quitar y CTA vacío conservados. Miniaturas actuales de 56 px contain sin placeholder, visor único compartido con delegación y retorno de foco. Restablecer sólo ante CartDataError, elimina exclusivamente la clave propia y requiere clic. 21 Django, 7 Node, 22 Chromium y Ruff correctos; recálculo/foco/scroll, cinco anchuras y axe. Captura 360 px inspeccionada. Regresión adicional verifica visor tras recálculo en CI. Archivos: cart/home/base/partials, CSS, catalog.js/cart.js/cart-core.js y pruebas. Próxima tarea: catálogo y páginas de 12.

Tarea 2 publicada: ba15ef147560a7805fadb7d908af2c5fc0c02d9d; CI success 38115123725. Tarea 3 publicada: d7da4e8424bcf88f20cc5c8e7dceb368884b8c8e; CI en curso al continuar.

Tarea 4 validada: placeholder solicitado, h1/label Categoría accesibles ocultos y rango real de resultados. Paginator existente de 12, GET/filtros/orden conservados. 13 Django y 22 Chromium correctos, Ruff OK; dataset aislado de 45 verifica cuatro rangos, desempate por PK, ausencia de duplicados, páginas inválidas/vacío/única y filtros. Navegador confirma navegación sin JS y visor de carrito después de recálculo. Captura compacta móvil inspeccionada; axe correcto. Archivos: views.py/home.html/test_views.py. Próxima tarea: limpieza visual de WhatsApp.

Tarea 3 CI success 38115244713. Tarea 4 publicada: bdf1661cb37eae5674a850b37f2a2b2a69c69544; CI en curso.

Tarea 5 validada: review-title oculto visualmente, conserva nombre accesible y foco. Párrafo redundante retirado; aviso obligatorio, textarea/copia/fallback y flujo vigentes intactos. 5 Django, 22 Chromium y Ruff correctos; axe, Escape/cancelación/copia/validación final sin envíos. Archivos: cart_review.html y test_whatsapp.py. Próxima tarea: seed exclusivamente manual en DEBUG, 45 productos sin fotos, simulación por defecto, --apply y --remove. Un manifiesto local en MEDIA_ROOT registra identidad/fingerprint de altas propias para no borrar comerciales ni demos editados; sin dependencias/modelos/migraciones nuevos.

Tarea 4 CI success 38115330273. Tarea 5 publicada: 3fb50fb00e0faaee8027ce8f55b6efdee90050f1; CI success 38115398369.

Tarea 6 validada: seed_demo_catalog manual en DEBUG, simulación sin escrituras, --apply, --remove y --remove --apply. Dataset JSON de 45 nombres representativos, 15 por categoría existente, kg 0.10/0.25 y unidad/paquete 1, precios ficticios, mayorista opcional/condiciones variadas, activos sin fotos. Resolución sin acentos/case exige categorías únicas activas; altas transaccionales. Manifiesto local de identidad/huella registra exclusivamente altas propias y excluye de limpieza demos editados, duplicados, registros ajenos y PK reutilizadas. Atomicidad de archivo y límite de interrupción documentados. No ejecutado sobre base comercial. 10 tests aislados correctos y Ruff OK: dry-run, 45/15, validación, idempotencia/renombre, categorías, producción, limpieza, manifiesto corrupto/perdido, rollback y regeneración. Archivos: comando/dataset/__init__, test_seed, README/spec. Próxima tarea: QA completa y paginación real en Chromium con fixtures Admin aislados.

Tarea 6 publicada: e008cbff27add19830a46b40190045e938bdb497; CI success 38115615142.

Tarea 7 QA completa: 78 Django, 7 Node y 24 Chromium correctos, check/Ruff OK y makemigrations sin cambios. Nuevas pruebas de lectura de storage bloqueada y datos null/duplicados, nombre largo/foto ausente tras Admin, visor tras recálculo; 45 fixtures explícitos mediante Admin aislado con cuatro páginas/rangos/IDs sin repetir, 15 por categoría, q/categoría y fallback GET sin JS. Se corrigió selector CSRF ambiguo del test (formulario vs logout), después suite completa de navegador correcta. Axe sin infracciones, cinco anchuras más 800, capturas reales/demo/cart/review/horarios/ubicación inspeccionadas. Mapa real visible, fotos existentes completas. Ningún mensaje enviado.

README/arquitectura/UX/spec/QA actualizados, historial conservado. Docker reconstruido sin cambiar volúmenes/.env. HTTP 200 /, /carrito/, /ubicacion/ y 301 antigua. Registros comerciales con huella idéntica antes/después, 6 productos/3 categorías/12 intervalos; seed no ejecutado sobre base comercial y sin manifiesto allí. QA detenido y bases descartables sin filas. Las tareas 1–6 publicadas con CI success. Pendiente publicar QA ampliada y comprobar su CI para cerrar la tarea 7.

## Cierre de nueva iteración UX/UI y datos de prueba

Tarea 7 publicada: 734b68192b5d5f4848c5072b96896fb9dec50d3f; CI completa success [38115967060](https://github.com/fitksh/Dulce-Salado/actions/runs/38115967060), incluidas las nuevas pruebas Chromium y capturas. Tareas 1–6 también publicadas con CI success, detalladas arriba. Las siete tareas solicitadas están completas, sin fallos de implementación conocidos.

Archivos principales: templates base/home/cart/cart_contents/cart_review/directions y visor compartido; CSS y catalog.js/cart.js/cart-core.js; views/urls; comando seed_demo_catalog, dataset y tests de comportamiento; README y los seis documentos. Modelos, migraciones, procesamiento de imágenes, Admin, reglas de precios/WhatsApp y dependencias conservados.

Verificación final: 78 Django, 7 Node, 24 Chromium; check/Ruff y migraciones correctos localmente y en CI. Entorno local actualizado, datos comerciales preservados, QA descartado, capturas inspeccionadas en cinco anchuras. Seed no aplicado a base comercial; opciones de simulación/alta/limpieza y límite conservador de demos editados/manifiesto explicados en README. Próximo paso: Ctrl+F5 y pruebas del dueño en teléfono/lector; actualizar dirección completa en Admin y ejecutar el seed sólo si desea esos datos ficticios. No hay fase futura anticipada.

Este commit cierra el roadmap documental; su propio hash y CI se consultan tras publicar, sin incluir un hash autorreferencial.

## Exportación PDF y ajustes puntuales — 2026-10-11

Solicitud y documentación obligatoria revisadas. main sincronizada; cambios locales previos en CSS (panel 260 px) y home (sin Mostrando) se conservan fuera de commits. Tareas secuenciales: header, PDF Admin, papelera, carrito desktop y QA. Sin modelos/migraciones ni cambios comerciales/fotográficos. Tarea 1 en curso: enlace Ubicación nombrado/aria-current, tres botones compactos con 44 px y cinco resoluciones más 320/800. Archivos base/CSS/tests. Las pruebas de rango comprueban datos semánticos para tolerar ambos textos del usuario.

Tarea 1 validada: 20 Django afectados, Ruff y 24 Chromium correctos; header 320/360/390/430/768/800/1280 sin overflow, tres enlaces con aria-current y objetivos ≥44 px, logo 64 px y horarios sin cambios. Capturas 320 y 800 inspeccionadas; axe correcto. Staging selectivo conserva cambios locales previos fuera de commits; tests de resultados independientes del prefijo editorial. Próxima tarea: PDF Admin mediante una implementación ReportLab, memoria y miniaturas Pillow temporales.

Tarea 1 publicada: 7734888; CI success [38151819941](https://github.com/fitksh/Dulce-Salado/actions/runs/38151819941).

Tarea 2: ReportLab 5.0.1 probado, único paquete nuevo directo, justificado en arquitectura. Dos rutas Admin GET con permisos view/change y botones que conservan filtros/búsqueda/orden; export_queryset compartido con CSV sin paginar. Módulo PDF común, A4 blanco, fuente Unicode, campos opcionales/ARS/inactivos/[DEMO], separadores y pie numerado/aviso comercial; miniaturas JPEG temporales 240 px/75 px visuales, sin modificar archivos. Casos sin foto/faltante/corrupta no abortan. Se corrigió una colisión real de caché de imágenes uniformes y se evita una página casi vacía antes de registros extensos. 13 tests PDF/CSV completos OK (Poppler disponible), Ruff OK. Ejemplos ficticios con/sin imágenes: 55.191/45.447 bytes, tres páginas cada uno, las seis PNG finales inspeccionadas; textos completos, proporciones/márgenes y paginación legibles. Descargas reales de ambas variantes añadidas a Chromium; su resultado completo se registra antes de publicar. Sin modelos/migraciones ni consultas/escrituras comerciales en generación de ejemplos.

Tarea 2 validación de navegador completa: 24/24 Chromium OK, descargas CSV/PDF reales con filtros conservados y archivos correctos; regresiones/axe correctas. check OK, makemigrations sin cambios, diff --check correcto. Publicación autorizada en main; cambios previos del usuario continúan fuera del commit.
