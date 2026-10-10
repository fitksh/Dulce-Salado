# Roadmap

Trabajar secuencialmente y actualizar el estado sólo al terminar y verificar cada etapa. No implementar etapas futuras por anticipado. En esta etapa se trabaja sólo en `main`.

- [x] Fase 0 — Definir alcance, decisiones técnicas y límites del MVP.
- [x] Fase 1 — Crear esqueleto local Django/PostgreSQL, Docker Compose, checks, CI y documentos para Codex. **Pendiente de validación local con Docker por el usuario**.
- [ ] Fase 2 — Modelar Category/Product, migraciones, Django Admin, validación y subida/optimización de imagen única. Resolver antes unidades e incrementos.
- [ ] Fase 3 — Catálogo público responsive, búsqueda por nombre/marca, filtros de categorías y estados vacíos.
- [ ] Fase 4 — Carrito local: cantidades, selector tipo de precio, `localStorage`, actualización de precios y totales.
- [ ] Fase 5 — Revisión, aviso obligatorio, mensaje `wa.me`, pruebas de flujo sin envío automático.
- [ ] Fase 6 — QA móvil, corrección de accesibilidad, optimización de imágenes y pruebas finales.
- [ ] Fase futura — VPS, dominio, HTTPS, proxy estáticos/media, backups y despliegue; fuera del alcance actual.

## Criterios de avance
Completar una fase significa código integrado en `main`, comprobaciones ejecutadas y registradas, criterios funcionales verificados y documentación actualizada. Si CI o tests no pudieron ejecutarse, el estado es pendiente de verificación.

## Primera tarea para Codex luego de esta entrega
Revisar estructura inicial, ejecutar checks y tests en Docker local, informar errores reales y corregir únicamente problemas del esqueleto. No crear modelos de catálogo hasta resolver las preguntas abiertas del `PRODUCT_SPEC.md`.
