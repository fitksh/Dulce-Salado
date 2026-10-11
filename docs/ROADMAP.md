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
