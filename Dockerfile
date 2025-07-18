FROM tiangolo/uwsgi-nginx:python3.12

ENV LISTEN_PORT=8080
EXPOSE 8080

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./bcource /app/bcource
COPY ./config.py /app/config.py
COPY ./run.py /app/run.py
COPY ./bcourse_docker/uwsgi.ini /app/uwsgi.ini

