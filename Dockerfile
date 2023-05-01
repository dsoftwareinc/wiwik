# pull official base image
FROM python:3.10.6-slim

# RUN apt update && apt install -y python3-dev gcc
# set work directory
WORKDIR /usr/src/app/

# set environment variables
ENV CRYPTOGRAPHY_DONT_BUILD_RUST 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt


# copy project
COPY forum/ /usr/src/app/
