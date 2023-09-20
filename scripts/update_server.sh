#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$SCRIPT_DIR/.."

if [[ "$CONTEXT" != "" ]]; then
  echo "context is $CONTEXT"
else
  echo "===> NO CONTEXT! Enter context for server or leave blank"
  read CONTEXT
fi

cd "$BASE_DIR" || exit
echo "[update_server.sh] Activating virtualenv"
source env/bin/activate || (echo "Couldn't activate virtualenv" && exit)
echo "[update_server.sh] Checking if there is a need to update requirements"
poetry export --without-hashes --with dev -o requirements.txt
pip install -r requirements.txt
rm requirements.txt

echo "[update_server.sh] Updating django data"
cd "$BASE_DIR/forum"
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py calculate_tag_stats

echo "[update_server.sh] Clean redis cache"
redis-cli KEYS "cache:*" | xargs redis-cli DEL

echo "[update_server.sh] Changing logs ownership"
touch ~/rqworker.log
touch ~/gunicorn.log
sudo chown syslog:adm ~/rqworker.log
sudo chown syslog:adm ~/gunicorn.log

echo "[update_server.sh] Updating rsyslog settings"
sudo cp $BASE_DIR/config/$CONTEXT/rsyslog.gunicorn.conf /etc/rsyslog.d/gunicorn.conf
sudo cp $BASE_DIR/config/$CONTEXT/rsyslog.rqworker.conf /etc/rsyslog.d/rqworker.conf

echo "[update_server.sh] Updating gunicorn service"
sudo cp $BASE_DIR/config/$CONTEXT/gunicorn.service /etc/systemd/system/gunicorn.service
echo "[update_server.sh] Updating rqworker service"
sudo cp $BASE_DIR/config/$CONTEXT/rqworker@.service /etc/systemd/system/rqworker@.service
sudo systemctl daemon-reload
echo "[update_server.sh] restarting gunicorn service"
sudo systemctl restart gunicorn
echo "[update_server.sh] stopping rqworker service 1"
sudo systemctl stop rqworker@1
echo "[update_server.sh] stopping rqworker service 2"
sudo systemctl stop rqworker@2
echo "[update_server.sh] stopping rqworker service 3"
sudo systemctl stop rqworker@3
echo "[update_server.sh] starting rqworker services 1..3"
sudo systemctl start rqworker@{1..2}

echo "[update_server.sh] Updating nginx"
sudo cp "$BASE_DIR/config/$CONTEXT/nginx.django_site.conf" "/etc/nginx/conf.d/django_site.conf"
sudo service nginx restart

cd "$BASE_DIR"
