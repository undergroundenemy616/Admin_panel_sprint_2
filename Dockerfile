FROM python:3.8 as MAIN
FROM MAIN as BUILDER
RUN apt update && apt install -y gcc python3-dev
COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt
RUN pip install pyarmor
RUN mkdir -p /var/source
WORKDIR /var/source
COPY . .
RUN pyarmor obfuscate --src="." --exclude venv -r --output=/var/distribute manage.py
COPY booking_api_django_new/environments /var/distribute/booking_api_django_new/environments
FROM MAIN
COPY --from=BUILDER /root/.local /root/.local
COPY --from=BUILDER /var/distribute /code
WORKDIR /code
ENV PATH=/root/.local/bin:$PATH
ENV BRANCH=master
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]