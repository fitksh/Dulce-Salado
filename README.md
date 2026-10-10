# Dulce y Salado

Catálogo comercial mobile-first para un pequeño negocio de repostería, dietética y cotillón. Los visitantes consultan productos y tarifas, arman un carrito local y abren WhatsApp con un mensaje de pedido precargado. **No es un e-commerce transaccional.**

**Estado:** base técnica y documentación. No se implementaron todavía productos, carrito ni integración WhatsApp.

## Documentos de trabajo
- [AGENTS.md](AGENTS.md): instrucciones para Codex.
- [Especificación funcional](docs/PRODUCT_SPEC.md).
- [Arquitectura](docs/ARCHITECTURE.md).
- [UX/UI](docs/UX_UI.md).
- [Roadmap](docs/ROADMAP.md).

## Requisitos
Docker Engine / Docker Desktop y Docker Compose.

## Inicio local
```sh
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```
Visitar `http://localhost:8000/` y `http://localhost:8000/admin/`.

Pruebas:
```sh
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose exec web ruff check .
```

Detener: `docker compose down`. Evitar `down -v` si querés conservar la base local.

## Forma de trabajo
Por ahora se usa únicamente `main`. Encargar una tarea concreta a Codex, hacerle leer primero `AGENTS.md` y los documentos vinculados; exigir tests y un resumen de cambios. No implementar fases futuras por anticipado.

## Despliegue
VPS, dominio, HTTPS y backup remoto deliberadamente pospuestos.
