# pull official base image
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

ADD https://astral.sh/uv/0.7.12/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# RUN apt update && apt install -y python3-dev gcc
# set work directory
WORKDIR /usr/src/app/

# set environment variables
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# copy project
COPY ./pyproject.toml .
COPY ./uv.lock .
COPY ./README.md .
RUN uv sync --locked
COPY forum/ /usr/src/app/
