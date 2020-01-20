# NOT TESTED YET

FROM python:3.7

RUN apt-get -y update && apt-get -y upgrade && \
   apt-get install --no-install-recommends -y wait-for-it

WORKDIR /app
COPY requirements.txt .
RUN pip install -U -r requirements.txt
COPY ./todolist ./todolist

EXPOSE 8000
COPY entrypoint /usr/local/bin
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
