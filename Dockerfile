FROM python:3.11.0-slim

RUN pip install poetry

COPY . /app
WORKDIR /app

RUN poetry install --no-root
