ARG CONTEXT=prod

FROM python:3.10.17-slim-bookworm as base

## Setup
ARG CONTEXT
WORKDIR /app
ENV ${CONTEXT}=1

## Context-based setup
### Add context value as a helper env variable
ENV ${CONTEXT}=1

### Query based on context value
ENV CONTEXT_INSTALLS=${tests:+"curl"}${prod:+"cron"}${dev:+""}
ENV REQUIREMENTS_FILE=${tests:+"testing"}${prod:+"general"}${dev:+"testing"}${debug:+"testing"}

## Install

RUN apt-get -y update && apt-get -y upgrade && apt-get install --no-install-recommends -y \
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

RUN pip install --no-cache-dir -U -r requirements-${REQUIREMENTS_FILE}.txt

ENV PYTHONPATH /app/

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

FROM base as tests

COPY scripts/* scripts/system/* tests/entrypoint.sh ./
COPY scripts/ci/* ./ci/

STOPSIGNAL SIGKILL



# Intermediate Image

FROM base as moduled

ARG MODULE
RUN test -n "$MODULE" || (echo "MODULE not set" && false)
ENV MODULE=$MODULE

ARG PORT
RUN test -n "$PORT" || (echo "PORT not set" && false)
ENV PORT=$PORT

EXPOSE $PORT

COPY $MODULE/entrypoint.sh ./



# Development Image

FROM moduled as dev

COPY scripts/system/* scripts/* ./


ENV FLASK_APP=datastore.$MODULE.app
ENV FLASK_DEBUG=1



# Debug Image

FROM moduled as debug

ENV FLASK_APP=datastore.$MODULE.app
ENV FLASK_DEBUG=1



# Production Image

FROM moduled as prod

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
