# Estado de ejecución — MVP

Fecha de inicio: 2026-10-10. Trabajo autorizado secuencial en `main` hasta completar el MVP.

## Tarea actual
Segunda iteración UX/UI en curso. Tarea 1: limpieza de textos y navegación. Historial MVP y primera etapa conservados; datos comerciales existentes intactos.

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
