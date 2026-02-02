FROM python:3.11-slim

LABEL maintainer="yooooonira"
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ./drf/requirements.txt /tmp/requirements.txt
COPY ./drf/requirements.dev.txt /tmp/requirements.dev.txt

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then /py/bin/pip install -r /tmp/requirements.dev.txt; fi && \
    rm -rf /tmp

COPY ./drf /app    

ENV PATH="/py/bin:$PATH"

RUN adduser --disabled-password --gecos "" django-user

USER django-user

EXPOSE 8000