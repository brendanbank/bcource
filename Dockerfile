FROM python:3.13-slim

RUN groupadd -r bcourse && useradd -r -g bcourse -d /app -s /sbin/nologin bcourse

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./bcource /app/bcource
COPY ./config.py /app/config.py
COPY ./run.py /app/run.py
COPY ./run_scheduler.py /app/run_scheduler.py

RUN chown -R bcourse:bcourse /app

USER bcourse

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
