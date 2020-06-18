FROM python:3.8.1

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y wait-for-it postgresql-client redis-tools

WORKDIR /app
ENV PYTHONPATH /app/

COPY system_tests/requirements.txt .
COPY shared/requirements.txt requirements-shared.txt
COPY reader/requirements.txt requirements-reader.txt
COPY writer/requirements.txt requirements-writer.txt
COPY requirements/* ./
RUN pip install -U -r requirements-testing.txt -r requirements-shared.txt -r requirements-reader.txt -r requirements-writer.txt 

COPY scripts/* ./
COPY scripts/tests-cleanup.sh cleanup.sh

COPY shared/shared shared
COPY reader/reader reader
COPY writer/writer writer

CMD ["pytest"]
