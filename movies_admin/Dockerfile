FROM python:3.9.6-slim-buster

WORKDIR /project
COPY requirements/ requirements/
RUN pip install -r requirements/production.txt
COPY . .
RUN echo yes | python manage.py collectstatic

RUN chmod +x entrypoint.sh
CMD ["/project/entrypoint.sh"]



