#!/bin/bash

set -e

_term() {
  echo "Caught SIGTERM signal!"
  kill -TERM "$child1" 2>/dev/null
  kill -TERM "$child2" 2>/dev/null
}

trap _term SIGTERM
trap _term SIGINT

python manage.py migrate
python manage.py createsuperuser --no-input || true

echo "Starting UDPReceiver..."
python -u UDPReceiver.py &
child1=$!
echo "Starting Django webserver..."
python -u manage.py runserver --noreload 0.0.0.0:3000 &
child2=$!

echo "Processes started successfully"
# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
