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
- [ ] Tarea 6 — WhatsApp en nueva pestaña con fallback seguro.
- [ ] Tarea 7 — QA, documentación y publicación final.
