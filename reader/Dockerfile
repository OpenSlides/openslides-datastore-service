FROM python:3.8.1

RUN apt-get -y update && apt-get -y upgrade && \
   apt-get install --no-install-recommends -y wait-for-it postgresql-client

WORKDIR /tmp
ARG REPOSITORY_URL=https://github.com/OpenSlides/openslides-datastore-service.git
ARG GIT_CHECKOUT=master
RUN git clone --no-checkout -- $REPOSITORY_URL .
RUN git checkout $GIT_CHECKOUT
RUN git pull
RUN mkdir /app
RUN mv shared/shared reader/reader reader/entrypoint.sh reader/requirements.txt requirements/requirements-general.txt /app

WORKDIR /app
RUN rm -rf /tmp
RUN pip install -U -r requirements-general.txt

EXPOSE 8001
ENV PYTHONPATH /app/

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8001", "reader.app:application"]
