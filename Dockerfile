FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG USER=booking-api
ARG PATH_TO_APP=/home/$USER/app

RUN groupadd --gid 2000 $USER \
 && useradd --uid 2000 \
            --gid $USER \
            --shell /bin/bash \
            --create-home $USER

RUN apt-get update \
 && apt-get install -y  \
                    libpq-dev \
                    python-dev \
                    gcc \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir \
                -r requirements.txt

RUN mkdir -p $PATH_TO_APP\
 && chown -R $USER:$USER \
             $PATH_TO_APP \
 && touch $PATH_TO_APP/simple_office.log \
 && chown $USER:$USER \
          $PATH_TO_APP/simple_office.log

COPY --chown=$USER:$USER . $PATH_TO_APP

WORKDIR $PATH_TO_APP
USER $USER
