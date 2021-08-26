FROM python:3.9.6-slim-buster

WORKDIR /project
COPY . .
RUN pip install -r requirements/production.txt
RUN chmod +x entrypoint.sh
CMD ["/project/entrypoint.sh"]



