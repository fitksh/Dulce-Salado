# Estado de ejecución — MVP

Fecha de inicio: 2026-10-10. Trabajo autorizado secuencial en `main` hasta completar el MVP.

## Tarea actual
SEGUNDA ITERACIÓN UX/UI COMPLETADA Y PUBLICADA. Siete tareas verificadas localmente y en CI (63 Django, 7 Node y 22 Chromium). Historial MVP y primera etapa conservados; datos comerciales existentes intactos. Pendientes sólo pruebas manuales comerciales/dispositivo real descritas en QA.md.

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
