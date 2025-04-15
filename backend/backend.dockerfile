FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7


RUN apt update

RUN apt install ffmpeg -y

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.5.0 POETRY_HOME=/opt/poetry python && \
cd /usr/local/bin && \
ln -s /opt/poetry/bin/poetry && \
poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"


COPY ./start.sh /start.sh

RUN chmod +x /start.sh

COPY ./gunicorn_conf.py /gunicorn_conf.py

COPY ./start-reload.sh /start-reload.sh

RUN chmod +x /start-reload.sh

COPY ./app /app

WORKDIR /app/

ENV PYTHONPATH=/app

EXPOSE 80
    


