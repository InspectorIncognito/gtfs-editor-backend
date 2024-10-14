TRY_LOOP=10

wait_for_port()
{
  local name="$1" host="$2" port="$3"
  local j=0
  while ! nc -z "$host" "$port" >/dev/null 2>&1 < /dev/null; do
    j=$((j+1))
    if [ $j -ge $TRY_LOOP ]; then
      echo >&2 "$(date) - $host:$port still not reachable, giving up"
      exit 1
    fi
    echo "$(date) - waiting for $name... $j/$TRY_LOOP"
    sleep 5
  done
}

# if image is running on aws environment (fargate)
if [ -n "$ECS_CONTAINER_METADATA_URI_V4" ];
then
  wait_for_port "redis" "127.0.0.1" "6379"
  wait_for_port "postgres" "$DB_HOST" "5432"
else
  wait_for_port "redis" "cache" "6379"
  wait_for_port "postgres" "db" "5432"
fi

case "$1" in
  webserver)
    echo "starting webserver"
    python manage.py migrate
    python manage.py collectstatic --no-input
    python manage.py compilemessages

    gunicorn --chdir gtfseditor --access-logfile - --bind :8000 gtfseditor.wsgi:application -t 1200
  ;;
  webserver-dev)
    echo "starting webserver"
    python manage.py migrate
    python manage.py collectstatic --no-input
    python manage.py compilemessages

    python ./manage.py runserver 0.0.0.0:8000
  ;;
  worker)
    echo "starting worker"
    python manage.py compilemessages
    python manage.py rqworker default gtfseditor --worker-class rqworkers.gtfseditorWorker.GTFSEditorWorker
  ;;
esac