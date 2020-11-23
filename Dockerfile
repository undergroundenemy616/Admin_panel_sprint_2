FROM python:3.7-alpine as MAIN
FROM MAIN as BUILDER
RUN apk update \
  && apk add --no-cache --virtual build-deps gcc python3-dev musl-dev \
  && apk add --no-cache jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
  && apk add --no-cache libffi-dev py-cffi postgresql-dev \
  && rm -rf /var/cache/apk/*
COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt
RUN pip install pyarmor
RUN pyarmor obfuscate --src="." --exclude venv -r --output=/var/distribute manage.py
FROM MAIN
COPY --from=BUILDER /root/.local /root/.local
COPY --from=BUILDER /var/distribute /code
WORKDIR /code
COPY booking_api_django_new/environments booking_api_django_new/environments
RUN apk update && apk add libpq postgresql-dev
ENV PATH=/root/.local/bin:$PATH
ENV BRANCH=master
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]