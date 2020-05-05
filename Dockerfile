FROM python:3.8.1

ARG USE_REDIS
ENV USE_REDIS=$USE_REDIS

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y wait-for-it postgresql-client ${USE_REDIS:+redis-tools}

WORKDIR /tmp
ARG REPOSITORY_URL=https://github.com/OpenSlides/openslides-datastore-service.git
ARG GIT_CHECKOUT=master

RUN git clone --no-checkout -- $REPOSITORY_URL .
RUN git checkout $GIT_CHECKOUT
RUN git pull
RUN mkdir /app
RUN mv shared/shared scripts/entrypoint.sh requirements/requirements-general.txt /app

ARG MODULE
RUN test -n "$MODULE" || (echo "MODULE not set" && false)
ENV MODULE=$MODULE

RUN mv $MODULE/$MODULE $MODULE/requirements.txt /app

WORKDIR /app
RUN rm -rf /tmp
RUN pip install -U -r requirements-general.txt

ARG PORT
RUN test -n "$PORT" || (echo "PORT not set" && false)
ENV PORT=$PORT

EXPOSE $PORT
ENV PYTHONPATH /app/

ENTRYPOINT ["./entrypoint.sh"]
CMD gunicorn -w 1 -b 0.0.0.0:$PORT $MODULE.app:application
