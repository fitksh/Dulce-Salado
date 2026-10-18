# Actualizar Dulce y Salado con carpeta local y Portainer

Guía para la instalación existente en `/mnt/datos/docker/dulce-salado`, rama `main`. Estos pasos son para el operador de la Raspberry; no se ejecutaron desde esta tarea. GitHub Actions valida código y no publica imágenes ni despliega el sitio.

## 1. Identificar y conservar la instalación

En Portainer, abrir el entorno de la Raspberry y el stack existente. En el contenedor **web**, revisar Inspect: etiquetas `com.docker.compose.project`, `com.docker.compose.project.config_files`, imagen y montajes. Conservar exactamente el nombre de proyecto, los archivos Compose/overrides, `.env`, puertos y los montajes PostgreSQL/media. No crear otro stack. Si figura como stack externo, operar su contenedor desde **Containers**.

Abrir SSH a la Raspberry. Usar el nombre de proyecto que muestra Portainer; `dulce-salado` es el valor habitual de esta carpeta, no cambiarlo si la instalación usa otro. Si se utilizan archivos Compose adicionales, conservar también `COMPOSE_FILE` con esos mismos archivos.

```sh
cd /mnt/datos/docker/dulce-salado
export COMPOSE_PROJECT_NAME='dulce-salado'
docker compose ps
git status --short --branch
```

Comprobar que `docker compose ps` muestra los mismos contenedores que Portainer. Si no coinciden, corregir nombre/archivos antes de continuar. Si hay cambios de código locales, conservarlos e integrarlos antes de actualizar; no usar reset, clean ni checkout forzado.

## 2. Detener sólo web y respaldar

En Portainer: **Containers → contenedor web del stack → Stop**. Mantener **db** iniciado y detener las escrituras administrativas durante la actualización.

En la misma sesión SSH:

```sh
set -eu
BACKUP_DIR="$PWD/.qa/backups/raspberry-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
cp .env "$BACKUP_DIR/env"
git rev-parse HEAD > "$BACKUP_DIR/commit-anterior.txt"
docker compose exec -T db sh -c 'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$BACKUP_DIR/postgresql.dump"
docker compose run --rm --no-deps web tar -C /app/media -czf - . > "$BACKUP_DIR/media.tar.gz"
docker compose exec -T db pg_restore --list < "$BACKUP_DIR/postgresql.dump" > "$BACKUP_DIR/postgresql-contenido.txt"
tar -tzf "$BACKUP_DIR/media.tar.gz" > "$BACKUP_DIR/media-contenido.txt"
```

Guardar además una copia privada del respaldo fuera de la Raspberry. El dump contiene los datos de esa instalación; publicar código de esta PC no transfiere sus productos, fotos, usuarios o `.env`.

## 3. Actualizar, construir y ensayar las migraciones

```sh
git pull --ff-only origin main
git rev-parse HEAD
docker compose build web
```

No sustituir el Compose adaptado a la Raspberry por el ejemplo de Windows. Revisar el hash contra la publicación informada. Un rechazo del pull debe resolverse conservando los cambios locales.

Esta versión incluye las migraciones 0005–0009 si la Raspberry todavía no las tiene. **0008 descarta centavos existentes sin redondear**; el respaldo es necesario para recuperarlos. 0005 normaliza el incremento a una presentación; las migraciones de mensajes conservan personalizaciones según sus reglas documentadas. No ejecutar seed ni reset.

Ensayar restauración y migración en una base nueva, con nombre exclusivo, dentro del mismo PostgreSQL:

```sh
RESTORE_DB="dys_restorecheck_$(date +%Y%m%d%H%M%S)"
docker compose exec -T db sh -c 'createdb -U "$POSTGRES_USER" "$1"' sh "$RESTORE_DB"
docker compose exec -T db sh -c 'pg_restore --exit-on-error --no-owner -U "$POSTGRES_USER" -d "$1"' sh "$RESTORE_DB" < "$BACKUP_DIR/postgresql.dump"
docker compose run --rm --no-deps -e POSTGRES_DB="$RESTORE_DB" web python manage.py migrate --noinput
docker compose run --rm --no-deps -e POSTGRES_DB="$RESTORE_DB" web python manage.py check
```

Si el ensayo falla, conservar la copia para diagnóstico y no migrar la base real. Tras comprobar el ensayo correcto, eliminar exclusivamente esa base temporal:

```sh
case "$RESTORE_DB" in
  dys_restorecheck_*) docker compose exec -T db sh -c 'dropdb -U "$POSTGRES_USER" "$1"' sh "$RESTORE_DB" ;;
  *) echo 'Nombre de base temporal inesperado'; exit 1 ;;
esac
```

## 4. Migrar la base real y recrear web desde Portainer

```sh
docker compose run --rm --no-deps web python manage.py migrate --noinput
docker compose run --rm --no-deps web python manage.py check
```

Volver a Portainer: **Containers → mismo contenedor web → Recreate**. Dejar desactivado **Pull latest image / Re-pull image**, porque `docker compose build web` acaba de construir la imagen local. Confirmar **Recreate** conservando la imagen configurada y todos los montajes/variables del contenedor existente. Si queda detenido, pulsar **Start**. No recrear PostgreSQL.

Si la instalación externa no permite esa operación desde la UI, el equivalente en la misma sesión y proyecto es:

```sh
docker compose up -d --no-deps web
```

**Restart** por sí solo no cambia la imagen de un contenedor existente. **Pull and redeploy** de un stack Git o la opción de descargar imágenes tampoco actualizan este checkout local ni equivalen a reconstruir su Dockerfile. [Documentación de Portainer](https://docs.portainer.io/user/docker/stacks/edit).

## 5. Comprobar

En Portainer, verificar **web** iniciado y **db** healthy; abrir **Logs** de web. En su consola `/bin/sh` ejecutar:

```sh
python manage.py check
python manage.py showmigrations catalog
```

Comprobar que están aplicadas 0005–0009. Abrir catálogo/Admin, hacer Ctrl+F5, revisar fotos/precios, carrito, copiado y preparación del mensaje; a 320 px no debe existir scroll horizontal. No se envía WhatsApp automáticamente.

No eliminar el stack ni los volúmenes. No usar `docker compose down -v`, `docker volume rm` ni limpiezas con volúmenes. Mantener los mismos `postgres_data`/`media_data` reales (o sus montajes ya configurados). Si hay que volver atrás, detener escrituras y evaluar el código y respaldo anteriores juntos: revertir el esquema no recupera centavos y una restauración puede descartar datos creados después.
