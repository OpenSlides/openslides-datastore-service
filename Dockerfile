FROM python:3.8.1 AS basis

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y wait-for-it postgresql-client redis-tools

WORKDIR /app

COPY shared/shared /app/shared/
COPY cli /app/cli/
COPY scripts/system /app/
COPY requirements/requirements-general.txt /app/


# Build Reader.
FROM basis AS reader

COPY reader/reader /app/reader
COPY reader/entrypoint.sh /app/
COPY reader/requirements.txt /app/

RUN pip install -U -r requirements-general.txt

EXPOSE 9010
ENV PYTHONPATH /app/

ENTRYPOINT ["./entrypoint.sh"]
CMD gunicorn -w 1 -b 0.0.0.0:9010 reader.app:application


# Build Writer.
FROM basis AS writer

COPY writer/writer /app/writer
COPY writer/entrypoint.sh /app/
COPY writer/requirements.txt /app/

RUN pip install -U -r requirements-general.txt

EXPOSE 9011
ENV PYTHONPATH /app/

ENTRYPOINT ["./entrypoint.sh"]
CMD gunicorn -w 1 -b 0.0.0.0:9011 writer.app:application
