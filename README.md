# Dulce y Salado

Catálogo web mobile-first para un comercio de repostería, dietética y cotillón. Los clientes consultan precios minoristas y mayoristas, arman un carrito local y preparan una consulta de pedido para WhatsApp. **No es un e-commerce con checkout.**

## Estado

Proyecto en desarrollo. Esta primera entrega incluye la base de Django, PostgreSQL y Docker Compose, junto con la especificación funcional y las reglas para Codex. No están implementados todavía los productos, el carrito ni la integración con WhatsApp.

## Documentos de referencia

- [AGENTS.md](AGENTS.md): instrucciones operativas obligatorias para Codex.
- [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md): alcance, reglas de negocio y criterios de aceptación.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): arquitectura y restricciones técnicas.
- [docs/UX_UI.md](docs/UX_UI.md): diseño mobile-first e identidad visual.
- [docs/ROADMAP.md](docs/ROADMAP.md): fases e hitos.

En caso de discrepancia, seguir el orden de precedencia descrito en AGENTS.md y pedir confirmación antes de cambiar alcance.

## Desarrollo local

Requiere Docker y Docker Compose.

1. Copiar `.env.example` a `.env`.
2. Ejecutar `docker compose up --build -d`.
3. Ejecutar `docker compose exec web python manage.py migrate`.
4. Crear el administrador con `docker compose exec web python manage.py createsuperuser`.
5. Abrir `http://localhost:8000/` y `http://localhost:8000/admin/`.

Para ejecutar las comprobaciones:

```sh
docker compose exec web python manage.py check
docker compose exec web python manage.py test
```

Detener los contenedores con `docker compose down` (sin `-v`, para conservar los datos locales).

## Desarrollo con Codex

Trabajamos directamente en `main` durante esta fase, sin ramas adicionales ni pull requests obligatorios. Darle **una tarea concreta por vez** con sus criterios de aceptación; Codex debe leer primero AGENTS.md y los documentos vinculados. Cada cambio debe superar las comprobaciones y quedar reflejado en el roadmap. No implementar características futuras por anticipado.

## Alcance excluido

No hay registro de clientes, control de stock, pagos, historial de pedidos, motor de reglas mayoristas, API REST externa ni despliegue a VPS. El envío final de WhatsApp depende de una acción del cliente y no se puede verificar desde la web.

## Licencia

A definir. No asumir que el contenido, las imágenes o el código tienen una licencia de reutilización.
