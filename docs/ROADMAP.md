# Roadmap

Trabajar secuencialmente y actualizar el estado sólo al terminar y verificar cada etapa. No implementar etapas futuras por anticipado. En esta etapa se trabaja sólo en `main`.

- [x] Fase 0 — Definir alcance, decisiones técnicas y límites del MVP.
- [x] Fase 1 — Esqueleto y auditoría verificados en Docker Python 3.12/PostgreSQL: 7 tests, checks y Ruff OK; migraciones base aplicadas. CI se comprueba después de publicar.
- [ ] Fase 2 — Modelar Category/Product, migraciones, Django Admin, validación y subida/optimización de imagen única. Resolver antes unidades e incrementos.
- [ ] Fase 3 — Catálogo público responsive, búsqueda por nombre/marca, filtros de categorías y estados vacíos.
- [ ] Fase 4 — Carrito local: cantidades, selector tipo de precio, `localStorage`, actualización de precios y totales.
- [ ] Fase 5 — Revisión, aviso obligatorio, mensaje `wa.me`, pruebas de flujo sin envío automático.
- [ ] Fase 6 — QA móvil, corrección de accesibilidad, optimización de imágenes y pruebas finales.
- [ ] Fase futura — VPS, dominio, HTTPS, proxy estáticos/media, backups y despliegue; fuera del alcance actual.

## Criterios de avance
Completar una fase significa código integrado en `main`, comprobaciones ejecutadas y registradas, criterios funcionales verificados y documentación actualizada. Si CI o tests no pudieron ejecutarse, el estado es pendiente de verificación.

## Continuación autorizada
Completar secuencialmente el MVP según la solicitud de desarrollo autónomo del 2026-10-10. Las decisiones de unidades, incrementos, mayorista opcional y centavos están autorizadas y registradas en `EXECUTION_STATUS.md`.
