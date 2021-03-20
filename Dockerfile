FROM python:3.8 as MAIN
RUN apt-get --allow-insecure-repositories update
RUN apt-get --allow-unauthenticated install -y gcc python3-dev
RUN apt-get --allow-unauthenticated install -y netcat-openbsd
COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt
RUN mkdir -p /var/source
WORKDIR /var/source
COPY . .
RUN chmod +x ./waiting_for_postgres.sh

COPY --from=BUILDER /root/.local /root/.local
COPY --from=BUILDER /var/source /code
WORKDIR /code
ENV PATH=/root/.local/bin:$PATH
ENV BRANCH=master
EXPOSE 8000
ENTRYPOINT [ "./waiting_for_postgres.sh" ]
