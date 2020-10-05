FROM python:3.8.5-slim-buster

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y wait-for-it gcc libpq-dev libc-dev postgresql-client redis-tools

WORKDIR /app
ENV PYTHONPATH /app/

ARG MODULE
RUN test -n "$MODULE" || (echo "MODULE not set" && false)
ENV MODULE=$MODULE

ARG PORT
RUN test -n "$PORT" || (echo "PORT not set" && false)
ENV PORT=$PORT
EXPOSE $PORT

COPY requirements/requirements-general.txt /app/
COPY $MODULE/requirements.txt .

RUN pip install -U -r requirements-general.txt

COPY cli cli
COPY shared/shared shared
COPY $MODULE/$MODULE $MODULE
COPY $MODULE/entrypoint.sh scripts/system/* ./

ENV NUM_WORKERS=1

ENTRYPOINT ["./entrypoint.sh"]
CMD gunicorn -w $NUM_WORKERS -b 0.0.0.0:$PORT $MODULE.app:application
