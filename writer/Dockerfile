FROM python:3.8.1

RUN apt-get -y update && apt-get -y upgrade && \
   apt-get install --no-install-recommends -y wait-for-it postgresql-client

WORKDIR /tmp
ARG REPOSITORY_URL=https://github.com/OpenSlides/openslides-datastore-service.git
ARG GIT_CHECKOUT=master
RUN git clone --no-checkout -- $REPOSITORY_URL .
RUN git checkout $GIT_CHECKOUT
WORKDIR /tmp/writer
RUN mkdir /app
RUN mv writer entrypoint.sh requirements.txt /app

WORKDIR /app
RUN rm -rf /tmp
RUN pip install -U -r requirements.txt

EXPOSE 8000
ENV PYTHONPATH /app/

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "writer.app:application"]
