# Instrucciones para Codex — Dulce y Salado

## Objetivo
Construir un catálogo comercial mobile-first para un pequeño comercio de repostería, dietética y cotillón. El cliente consulta precios, arma un carrito local y prepara un mensaje de WhatsApp. No es un e-commerce y no confirma pedidos.

## Lectura obligatoria
Antes de modificar código, leer: `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/UX_UI.md` cuando la tarea afecte interfaz y `docs/ROADMAP.md`. Orden de autoridad: indicación explícita del usuario > `PRODUCT_SPEC.md` > `ARCHITECTURE.md` > `UX_UI.md` > `ROADMAP.md` > decisiones de implementación. Si hay contradicciones, informar y pedir decisión antes de desarrollar.

## Flujo de trabajo
- Trabajar directamente en `main` durante desarrollo; no crear ramas ni PR salvo petición expresa.
- Implementar exclusivamente la tarea solicitada. No anticipar fases del roadmap.
- Antes de cambiar código, resumir alcance, archivos afectados y criterios de aceptación. Si existe ambigüedad que afecte reglas de negocio, consultar.
- Preferir cambios pequeños, legibles, idiomáticos, sin abstracciones prematuras. YAGNI y KISS.
- No introducir nuevas dependencias, servicios o modelos sin justificar la necesidad para la tarea.
- No modificar archivos ajenos a la tarea ni reorganizar arquitectura por preferencia personal.
- Añadir o actualizar tests de comportamiento en tareas funcionales. Mantener migraciones versionadas si se modifican modelos.
- Ejecutar `python manage.py check`, tests y lint, o informar explícitamente si no pueden ejecutarse. No afirmar que pasaron sin ejecución real.
- Al finalizar, explicar archivos cambiados, pruebas realizadas, limitaciones y siguiente paso concreto. Marcar el progreso real en `docs/ROADMAP.md`.

## Tecnología aprobada
Python 3.12, Django 5.2 LTS, PostgreSQL, templates Django, CSS, JavaScript vanilla, Django Admin, Docker Compose. `localStorage` para carrito. Una aplicación Django monolítica.

## Prohibido salvo autorización expresa
React, Vue, Svelte, SPA, DRF, GraphQL, Celery, Redis, microservicios, cuentas de clientes, pedidos persistidos, inventario, pagos, envíos, facturación, reglas automáticas de mayorista, imágenes múltiples por producto, API de WhatsApp Business, analítica avanzada, PWA, integración cloud storage o infraestructura VPS.

## Negocio y seguridad
- El mayorista lo selecciona el cliente manualmente; por defecto minorista, sin evaluar automáticamente condiciones. Se avisa que corresponde confirmación comercial.
- Los precios son estimativos, en ARS, y la disponibilidad se consulta al comercio.
- No almacenar precios como autoridad en `localStorage`; refrescar desde catálogo vigente al abrir/revisar el carrito.
- No crear pedidos ni afirmar que el WhatsApp fue enviado. `wa.me` precarga un mensaje, cuyo envío hace el cliente.
- Admin sólo con autenticación de Django; no exponer `/media` para escritura anónima. Validar archivos de imagen cuando se implemente carga.
- No guardar credenciales ni `.env` en Git. Variables de entorno para secretos.
- Mantener accesibilidad, diseño mobile-first, URLs y HTML semánticos, y tests razonables.

## Uso de GitHub
Se trabaja sólo en `main`. Se permiten commits pequeños asociados a tareas; no exigir issues ni PR para cada cambio. No forzar push, no reescribir historia sin autorización.
