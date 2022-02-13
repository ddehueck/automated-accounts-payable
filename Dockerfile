
FROM python:3.8

# Weird where IN_DEPLOYMENT passed as arg needs to be set as arg again?
ARG IN_DEPLOYMENT=${IN_DEPLOYMENT}

ENV IN_DEPLOYMENT=${IN_DEPLOYMENT} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.1.8

# System deps:
RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /
COPY poetry.lock pyproject.toml /

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install $(test "$IN_DEPLOYMENT" == "true" && echo "--no-dev") --no-interaction --no-ansi

# Creating folders, and files for a project:
COPY . /

# Upgrade DB - in deployment only - part of elastic beanstalk CD
RUN if [ "$IN_DEPLOYMENT" = "true" ]; then alembic upgrade head; fi;