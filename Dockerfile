FROM python:3.7-alpine as MAIN
FROM MAIN as BUILDER
RUN apk update \
  && apk add --no-cache --virtual build-deps gcc python3-dev musl-dev \
  && apk add --no-cache jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
  && apk add --no-cache libffi-dev py-cffi \
  && rm -rf /var/cache/apk/*
COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt

FROM MAIN
COPY --from=BUILDER /root/.local /root/.local
WORKDIR /code
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8080
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]