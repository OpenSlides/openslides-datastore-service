FROM python:3.8.1

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y wait-for-it postgresql-client redis-tools

WORKDIR /app
ENV PYTHONPATH /app/

COPY system_tests/requirements.txt requirements-general.txt
COPY requirements/requirements-testing.txt .
RUN pip install -U -r requirements-testing.txt

COPY scripts/* ./

CMD ["pytest"]
