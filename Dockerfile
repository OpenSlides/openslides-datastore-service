FROM python:3.10.13-slim-bookworm

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y wait-for-it gcc libpq-dev libc-dev postgresql-client redis-tools

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
ENV NUM_THREADS=5
ENV WORKER_TIMEOUT=30

LABEL org.opencontainers.image.title="OpenSlides Datastore Service"
LABEL org.opencontainers.image.description="Service for OpenSlides which wraps the database, which includes reader and writer functionality."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/OpenSlides/openslides-datastore-service"

HEALTHCHECK CMD python cli/healthcheck.py

ENTRYPOINT ["./entrypoint.sh"]
CMD exec gunicorn -w $NUM_WORKERS -k gthread --threads $NUM_THREADS -b 0.0.0.0:$PORT datastore.$MODULE.app:application -t $WORKER_TIMEOUT
