#!/bin/bash

python manage.py migrate
python manage.py collectstatic --noinput

#touch /srv/logs/gunicorn.log
#touch /srv/logs/access.log
#tail -n 0 -f ./logs/*.log &

echo "Starting gunicorn"
exec gunicorn AstroSite.wsgi:application \
	--name AstroSite \
	--workers 3 \
	--log-level=info \
	"$@"

#exec python manage.py runserver
