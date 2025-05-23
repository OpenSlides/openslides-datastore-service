FROM python:3.10.17-slim-bookworm

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y ncat gcc libpq-dev libc-dev postgresql-client redis-tools cron

WORKDIR /app
ENV PYTHONPATH /app/

COPY requirements/requirements-general.txt /app/

RUN pip install -U -r requirements-general.txt

COPY cli cli
COPY datastore datastore

ARG PORT
RUN test -n "$PORT" || (echo "PORT not set" && false)
ENV PORT=$PORT
EXPOSE $PORT

ARG MODULE
RUN test -n "$MODULE" || (echo "MODULE not set" && false)
ENV MODULE=$MODULE

COPY $MODULE/entrypoint.sh scripts/system/* ./

ENV NUM_WORKERS=1
ENV WORKER_TIMEOUT=30

RUN echo "20 4 * * * root /app/cron.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/trim-collectionfield-tables

LABEL org.opencontainers.image.title="OpenSlides Datastore Service"
LABEL org.opencontainers.image.description="Service for OpenSlides which wraps the database, which includes reader and writer functionality."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/OpenSlides/openslides-datastore-service"

HEALTHCHECK CMD python cli/healthcheck.py

ENTRYPOINT ["./entrypoint.sh"]
CMD exec gunicorn -w $NUM_WORKERS -b 0.0.0.0:$PORT datastore.$MODULE.app:application -t $WORKER_TIMEOUT
