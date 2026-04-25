FROM python:3.13-slim

RUN groupadd -r bcourse && useradd -r -g bcourse -d /app -s /sbin/nologin bcourse

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./bcource /app/bcource
COPY ./config.py /app/config.py
COPY ./run.py /app/run.py
COPY ./run_scheduler.py /app/run_scheduler.py
COPY ./migrations /app/migrations

# Compile translations at build time (.mo files are gitignored)
RUN pybabel compile -d /app/bcource/translations

RUN chown -R bcourse:bcourse /app

USER bcourse

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=8); sys.exit(0 if r.status==200 else 1)"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
