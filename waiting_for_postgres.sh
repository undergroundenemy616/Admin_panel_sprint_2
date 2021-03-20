#!/bin/bash
echo "Waiting for postgres..."
while ! nc -z $HOST $PORT; do
  sleep 0.1
done
echo "PostgreSQL started"
python init_db.py
exec "$@"