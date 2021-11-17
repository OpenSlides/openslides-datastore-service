FROM python:3.8.1

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y wait-for-it postgresql-client redis-tools

WORKDIR /app
ENV PYTHONPATH /app/

COPY system_tests/requirements.txt .
COPY requirements/* ./
RUN pip install -U -r requirements.txt -r requirements-testing.txt

COPY scripts/* ./
COPY scripts/ci/* ./ci/

COPY datastore datastore
COPY tests tests

RUN mkdir -p /run/secrets
RUN echo -n openslides >/run/secrets/datastore_postgres_user
RUN echo -n openslides >/run/secrets/datastore_postgres_password

ARG CHOWN
RUN chown -R $CHOWN /app

CMD ["pytest", "system_tests"]
