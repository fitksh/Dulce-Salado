# Estado de ejecución — MVP

Fecha de inicio: 2026-10-10. Trabajo autorizado secuencial en `main` hasta completar el MVP.

## Tarea actual
MVP LISTO PARA PRUEBAS LOCALES. Fases 0–6 completadas; implementación publicada en main y CI ampliada verificada.

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
