# Estado de ejecución — MVP

Fecha de inicio: 2026-10-10. Trabajo autorizado secuencial en `main` hasta completar el MVP.

## Tarea actual
Fase 4 completada: carrito local con cálculo vigente en servidor. Siguiente: revisión y WhatsApp.

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
- Pendientes: WhatsApp; QA final visual y accesibilidad.

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

## Publicación
Último commit publicado: `1486025` (catálogo). Modelos `1813f7b`: CI success, run `38084873987`. Auditoría `50ef9b0`: CI success, run `38084761552`. Cada commit siguiente incluye el avance verificado y el identificador del commit anterior; el HEAD exacto se consulta con `git log -1`.

## Bloqueos
Ninguno de implementación. El número real de WhatsApp deberá configurarlo el dueño.

## Próxima tarea exacta
Publicar carrito y desarrollar revisión/aviso obligatorio con mensaje WhatsApp de datos actuales.
