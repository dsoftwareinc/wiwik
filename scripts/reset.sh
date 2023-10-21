#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$SCRIPT_DIR/.."
INITIAL_DB="$BASE_DIR/private/db2023-10-18.sqlite3"
echo "[reset.sh] Activating virtualenv"
source "$BASE_DIR/env/bin/activate" || (echo "Couldn't activate virtualenv" && exit)
cd $BASE_DIR || exit

echo "[reset.sh] Checking if there is a need to update requirements"
pip install poetry
poetry update

echo "[reset.sh] Removing previous database if exists"
rm "$BASE_DIR/forum/db.sqlite3"
echo "[reset.sh] Reseting to sample database"
cp "$INITIAL_DB" "$BASE_DIR/forum/db.sqlite3"
cd "$BASE_DIR/forum"
python manage.py makemigrations wiwik_lib badges forum similarity spaces tags userauth
python manage.py migrate

echo "[reset.sh] Creating google authentication system for site"
python manage.py create_social_apps
echo "[reset.sh] Reseting all users password to 1111"
python manage.py reset_users
#echo "[reset.sh] Creating sample data for tags"
#python manage.py create_sample_tags
#echo "[reset.sh] Creating sample users in the system"
#python manage.py create_sample_users
#echo "[reset.sh] Creating sample data for the forum"
#python manage.py load_json ../data.json

cd "$BASE_DIR"
