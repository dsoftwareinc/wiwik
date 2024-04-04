# pull official base image
FROM python:3.12.2-slim

# RUN apt update && apt install -y python3-dev gcc
# set work directory
WORKDIR /usr/src/app/

# set environment variables
ENV CRYPTOGRAPHY_DONT_BUILD_RUST 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
RUN pip install poetry
# copy project
COPY ./pyproject.toml .
RUN poetry export --without-hashes --with dev -o req.txt
COPY forum/ /usr/src/app/
RUN pip install -r req.txt
