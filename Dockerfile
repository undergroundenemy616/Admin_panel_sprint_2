FROM python:3.8
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

RUN apt-get --allow-insecure-repositories update
RUN apt-get --allow-unauthenticated install -y gcc python3-dev
RUN apt-get --allow-unauthenticated install -y netcat-openbsd


COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt
WORKDIR /code
COPY . .
RUN chmod +x ./waiting_for_postgres.sh
ENV PATH=/root/.local/bin:$PATH
ENV BRANCH=master
EXPOSE 8000
ENTRYPOINT [ "./waiting_for_postgres.sh" ]