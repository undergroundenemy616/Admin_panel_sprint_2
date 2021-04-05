FROM python:3.8
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get install -y gcc python3-dev

COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt
WORKDIR /code
COPY . .
ENV PATH=/root/.local/bin:$PATH
ENV BRANCH=master
EXPOSE 8000