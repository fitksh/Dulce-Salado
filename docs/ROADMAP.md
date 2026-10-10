# Roadmap

Trabajar secuencialmente y actualizar el estado sólo al terminar y verificar cada etapa. No implementar etapas futuras por anticipado. En esta etapa se trabaja sólo en `main`.

- [x] Fase 0 — Definir alcance, decisiones técnicas y límites del MVP.
- [x] Fase 1 — Esqueleto y auditoría verificados en Docker Python 3.12/PostgreSQL: 7 tests, checks y Ruff OK; migraciones base aplicadas. CI se comprueba después de publicar.
- [x] Fase 2 — Category/Product, migraciones, Admin con permisos e imagen única validada/optimizada. Verificado en Docker: 20 tests, checks y Ruff OK. Unidades e incrementos autorizados documentados.
- [x] Fase 3 — Catálogo público mobile-first, búsqueda, categorías y estados vacíos; 27 tests/check/Ruff OK. QA visual final en fase 6.
- [x] Fase 4 — Carrito local, cantidades/tarifa, refresco de datos y cálculos Decimal; 34 tests Django y 4 Node/check/Ruff OK.
- [ ] Fase 5 — Revisión, aviso obligatorio, mensaje `wa.me`, pruebas de flujo sin envío automático.
- [ ] Fase 6 — QA móvil, corrección de accesibilidad, optimización de imágenes y pruebas finales.
- [ ] Fase futura — VPS, dominio, HTTPS, proxy estáticos/media, backups y despliegue; fuera del alcance actual.

## Criterios de avance
Completar una fase significa código integrado en `main`, comprobaciones ejecutadas y registradas, criterios funcionales verificados y documentación actualizada. Si CI o tests no pudieron ejecutarse, el estado es pendiente de verificación.

## Continuación autorizada
Completar secuencialmente el MVP según la solicitud de desarrollo autónomo del 2026-10-10. Las decisiones de unidades, incrementos, mayorista opcional y centavos están autorizadas y registradas en `EXECUTION_STATUS.md`.
