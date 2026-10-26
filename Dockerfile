FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ARG REVISION=unknown
LABEL org.opencontainers.image.revision=$REVISION
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# A disposable build-only value; runtime still requires its real environment key.
RUN DJANGO_SECRET_KEY=collectstatic-build-only python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
