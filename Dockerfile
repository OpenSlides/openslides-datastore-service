ARG CONTEXT=prod

FROM python:3.10.19-slim-bookworm AS base

## Setup
ARG CONTEXT
WORKDIR /app
ENV APP_CONTEXT=${CONTEXT}

## Install
RUN CONTEXT_INSTALLS=$(case "$APP_CONTEXT" in \
    tests)  echo "curl";; \
    dev)    echo "";; \
    *)      echo "cron" ;; esac) && \
    apt-get -y update && apt-get -y upgrade && apt-get install --no-install-recommends -y \
    gcc \
    libc-dev \
    libpq-dev \
    ncat \
    postgresql-client \
    redis-tools \
    ${CONTEXT_INSTALLS} && \
    rm -rf /var/lib/apt/lists/*

## Requirements
COPY requirements/* scripts/system/* scripts/* ./
RUN  REQUIREMENTS_FILE=$(case "$APP_CONTEXT" in \
    tests) echo "testing";; \
    dev)   echo "testing";; \
    debug) echo "testing";; \
    *)     echo "general" ;; esac) && \
    pip install --no-cache-dir -U -r requirements-${REQUIREMENTS_FILE}.txt

ENV PYTHONPATH=/app/

## External Information
LABEL org.opencontainers.image.title="OpenSlides Datastore Service"
LABEL org.opencontainers.image.description="Service for OpenSlides which wraps the database, which includes reader and writer functionality."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/OpenSlides/openslides-datastore-service"

## Command
COPY ./dev/command.sh ./
RUN chmod +x command.sh
CMD ["./command.sh"]
HEALTHCHECK CMD python cli/healthcheck.py
ENTRYPOINT ["./entrypoint.sh"]

# Testing Image

FROM base AS tests

COPY scripts/* scripts/system/* tests/entrypoint.sh ./
COPY scripts/ci/* ./ci/
COPY dev ./dev/

STOPSIGNAL SIGKILL

# Intermediate Image

FROM base AS moduled

ARG MODULE
RUN test -n "$MODULE" || (echo "MODULE not set" && false)
ENV MODULE=$MODULE

ARG PORT
RUN test -n "$PORT" || (echo "PORT not set" && false)
ENV PORT=$PORT

EXPOSE $PORT

COPY $MODULE/entrypoint.sh ./

# Development Image

FROM moduled AS dev

COPY scripts/system/* scripts/* ./

ENV FLASK_APP=datastore.$MODULE.app
ENV FLASK_DEBUG=1

# Debug Image

FROM moduled AS debug

ENV FLASK_APP=datastore.$MODULE.app
ENV FLASK_DEBUG=1

# Production Image

FROM moduled AS prod

# Add appuser
RUN adduser --system --no-create-home appuser && \
    chown appuser /app/

COPY cli cli
COPY datastore datastore

COPY scripts/system/* ./

ENV NUM_WORKERS=1
ENV WORKER_TIMEOUT=30

RUN echo "20 4 * * * root /app/cron.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/trim-collectionfield-tables

USER appuser
