# Datos locales con fotos y presentaciones — 17/10/2026

La carga local tiene 45 fichas sin [DEMO] en el título: 12 de Dietética, 3 de Cotillón y 30 de Repostería. Se usan las nueve imágenes del directorio provisto por el dueño, copiadas a un directorio privado de trabajo; los originales de Descargas conservan exactamente sus SHA-256. Hay 45 rutas WebP independientes y nueve contenidos fotográficos distintos. Las imágenes están asociadas al producto correspondiente, con dos vistas alternadas del baño con leche.

Los productos alimenticios tienen seis presentaciones con el mismo título: 100 gr, kg, paquete de 500 gr, caja de 5 kg, pack de 3 paquetes y bolsa de 2 kg. Las cajas de regalo tienen caja individual, pack y paquete. Precios, pesos de las presentaciones y condiciones son datos ficticios de simulación, no oferta comercial confirmada. La marca se toma del producto fotografiado cuando resulta identificable; no se inventa una marca para la crema de chocolate.

Ejemplo de Baño de repostería blanco:

| Título | Unidad | Descripción | Precio de prueba |
| --- | --- | --- | --- |
| Baño de repostería blanco | 100 gr | Porción de 100 gr. | $ 1.040,00 |
| Baño de repostería blanco | kg | Venta por kilogramo. | $ 10.400,00 |
| Baño de repostería blanco | paquete | Paquete de 500 gr. | $ 5.200,00 |

Cada ficha tiene su propio ID, precio, cantidad e imagen. Sumar/quitar una no modifica las otras; descripción y unidad distinguen las presentaciones en carrito y WhatsApp. Se mantiene incremento fijo 1, sin conversiones automáticas ni fracciones.

## Repetir la simulación o carga

El seeder continúa manual, con DEBUG=True y simulación por defecto. Exige categorías activas existentes y conserva datos comerciales, ediciones e identidades dudosas. Los registros ya creados no se actualizan al cambiar fuentes o mapa.

En esta PC, las copias de entrada y el mapa están en .qa, fuera de Git:

```powershell
docker compose exec -T web python manage.py seed_demo_catalog --images-dir /app/.qa/seed-sources-20261017 --image-map /app/.qa/seed-image-map-20261017.json
docker compose exec -T web python manage.py seed_demo_catalog --images-dir /app/.qa/seed-sources-20261017 --image-map /app/.qa/seed-image-map-20261017.json --apply
```

La segunda ejecución sobre la carga actual crea cero fichas y conserva las 45 existentes. --remove sigue siendo una limpieza conservadora con simulación/--apply, no un vaciado general. Nunca se ejecuta en startup/migraciones. Para otra PC, copiar las fuentes/mapa a un directorio privado o montarlas en lectura; no subir fotografías/respaldos a Git. Actualizar el código antes de usar --image-map. Sin nuevos modelos, migraciones o dependencias por este cambio; no se accedió ni desplegó en Raspberry.

## Formato del mapa

JSON con todos los títulos del conjunto de semillas. Cada valor es un nombre de archivo presente en el directorio, o una lista para alternar vistas del mismo producto. No admite rutas externas; faltantes o nombres desconocidos cancelan el lote antes de escribir. Ejemplo parcial ilustrativo (el mapa real debe incluir todos los títulos):

```json
{
  "Baño de repostería blanco": "foto-blanco.jpeg",
  "Baño de repostería con leche": ["foto-leche-1.jpeg", "foto-leche-2.jpeg"]
}
```

Sin mapa continúa el reparto equilibrado/reproducible previo. En la carga real con mapa se prioriza que cada fotografía corresponda al producto, por lo que no se exige igual número de usos para cada foto.

## Manifiesto y datos anteriores

La versión 2 usa identidad categoría/título/unidad/descripción, permitiendo títulos repetidos. Conserva las verificaciones de procedencia por PK/fecha/huellas y la protección de ediciones, duplicados reales y fotos compartidas. Un manifiesto v1 aborta sin escribir ni adoptar registros por nombre: respaldar y revisar/limpiar con una revisión compatible o una operación específica autorizada. No borrar el manifiesto para forzar propiedad sobre datos anteriores.

En esta PC se eliminaron únicamente los 45 productos y tres categorías anteriores, conservando exactamente usuarios, configuración comercial/WhatsApp y horarios. No se reiniciaron secuencias: carritos antiguos no apuntan a productos nuevos por reutilización de IDs. Primero se restauró el respaldo y ensayó toda la operación sobre dulce_salado_seed_photos_check_20261017 con media temporal; luego se guardó el respaldo inmediato, se aplicó a dulce_salado y se comprobó repetición sin cambios. La operación puntual permanece privada en .qa, sin incorporar un reset general a la aplicación.

Respaldos en .qa/backups/20261017-real-photos/: database-before-apply.dump y media-before-apply.tar.gz son la copia inmediata anterior; database.dump/media.tar.gz son el respaldo inicial restaurado en el ensayo. checksums.json, source-checksums.json, rehearsal-result.json y reset-result.json registran huellas/conteos y conservación. Copias de trabajo y mapa también privados, ignorados por Git. Servidor habitual disponible en http://localhost:8000/; la copia de ensayo y el servidor QA se retiran al terminar.

## Verificación

29 pruebas del seeder y 175 Django completos correctos, 44 Chromium completos, check/Ruff/migraciones/diff correctos. La corrida en imagen auxiliar omitió 16 inspecciones PDF por ausencia de Poppler; la ejecución final en el contenedor habitual pasó las 175 sin omisiones. Prueba real con las fotos cargadas: seis títulos iguales para el producto blanco, selección independiente de 100 gr/kg/paquete, total inicial $ 16.640,00, incremento/decremento de kg y eliminación de 100 gr sin alterar las otras fichas; texto WhatsApp correcto y sin [DEMO]. Axe sin incidencias automáticas y sin desbordes en cinco anchos. Capturas seed-photos-presentations-1440/390 y seed-photos-cart-1440 inspeccionadas en .qa/screenshots/. Ningún WhatsApp enviado.

Archivos: catalog/management/demo_products.json, management/commands/seed_demo_catalog.py, catalog/test_seed.py, tests/browser.spec.cjs y documentación. Cambios locales en main; sin commit/push/despliegue en esta iteración.

El 18/10/2026 los precios del seed pasan a pesos enteros. 0008 conserva las 45 fichas/fotos locales y descarta centavos por decisión del dueño; no se ejecuta seed ni limpieza. Manifiesto previo intacto: --apply preserva fichas identificadas sin duplicarlas y --remove conserva cualquier huella que ya no coincida, sin asumir propiedad nueva. Ver PRECIOS_ENTEROS.md.
