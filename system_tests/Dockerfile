FROM python:3.10.13-slim-bookworm

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y ncat gcc libpq-dev libc-dev postgresql-client redis-tools

WORKDIR /app
ENV PYTHONPATH /app/

COPY system_tests/requirements.txt .
COPY requirements/* ./
RUN pip install -U -r requirements.txt -r requirements-testing.txt

COPY scripts/* ./
COPY scripts/ci/* ./ci/

COPY datastore datastore
COPY tests tests

ARG CHOWN
RUN chown -R $CHOWN /app

CMD ["pytest", "system_tests"]
