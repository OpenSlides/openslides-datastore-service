FROM python:3.8.1

RUN apt-get -y update && apt-get -y upgrade && \
   apt-get install --no-install-recommends -y wait-for-it postgresql-client

WORKDIR /app
COPY requirements.txt .
RUN pip install -U -r requirements.txt
COPY ./writer ./writer
COPY prod-entrypoint.sh .

EXPOSE 8000
ENV PYTHONPATH /app/

ENTRYPOINT ["./prod-entrypoint.sh"]
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "writer.app:application"]
